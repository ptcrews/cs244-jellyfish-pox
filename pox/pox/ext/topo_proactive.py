# Copyright 2013 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Installs forwarding rules based on topologically significant IP addresses.

We also issue those addresses by DHCP.  A host must use the assigned IP!
Actually, the last byte can be almost anything.  But addresses are of the
form 10.switchID.portNumber.x.

This is an example of a pretty proactive forwarding application.

The forwarding code is based on l2_multi.

Depends on openflow.discovery
Works with openflow.spanning_tree (sort of)
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt

from pox.lib.addresses import IPAddr,EthAddr,parse_cidr
from pox.lib.addresses import IP_BROADCAST, IP_ANY
from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.proto.dhcpd import DHCPLease, DHCPD
from collections import defaultdict
from pox.openflow.discovery import Discovery
import time
from construct_paths import Paths

log = core.getLogger("f.t_p")


# Adjacency map.  [sw1][sw2] -> port from sw1 to sw2
adjacency = defaultdict(lambda:defaultdict(lambda:None))

# Switches we know of.  [dpid] -> Switch and [id] -> Switch
switches_by_dpid = {}
switches_by_id = {}

# [sw1][sw2] -> (distance, intermediate)
path_map = defaultdict(lambda:defaultdict(lambda:(None,None)))

paths = Paths(log)

def dpid_to_mac (dpid):
  return EthAddr("%012x" % (dpid & 0xffFFffFFffFF,))

def compute_paths():
    log.debug("Timer fired: COMPUTING PATHS")
    log.debug("Vals: " + str(switches_by_dpid.values()))
    for adj1 in adjacency:
        for adj2 in adjacency[adj1]:
            log.debug("Adjacency: " + str(adj1) + " " + str(adj2) + " "  + str(adjacency[adj1][adj2]))
    paths.compute_paths(switches_by_dpid.values(), adjacency, log)
    log.debug("Timer fired: END COMPUTING PATHS")
    for sw in switches_by_dpid.itervalues():
      log.debug("In table sending")
      sw.send_table()
    log.debug("After table sending")

def _get_paths (src, dst):
    if src == dst:
        return [[]]
    else:
        return paths.get_paths(log, path_map, switches_by_dpid.values(), adjacency, src, dst)


def ipinfo (ip):
  parts = [int(x) for x in str(ip).split('.')]
  ID = parts[1]
  port = parts[2]
  num = parts[3]
  return switches_by_id.get(ID),port,num


class TopoSwitch (DHCPD):
  _eventMixin_events = set([DHCPLease])
  _next_id = 100

  def __repr__ (self):
    try:
      return "[%s/%s]" % (dpid_to_str(self.connection.dpid),self._id)
    except:
      return "[Unknown]"


  def __init__ (self):
    self.log = log.getChild("Unknown")

    self.connection = None
    self.ports = None
    self.dpid = None
    self._listeners = None
    self._connected_at = None
    self._id = None
    self.subnet = None
    self.network = None
    self._install_flow = False
    self.mac = None

    self.ip_to_mac = {}

    # Listen to our own event... :)
    self.addListenerByName("DHCPLease", self._on_lease)

    core.ARPHelper.addListeners(self)


  def _handle_ARPRequest (self, event):
    if ipinfo(event.ip)[0] is not self: return
    event.reply = self.mac


  def send_table (self):
    if self.connection is None:
      self.log.debug("Can't send table: disconnected")
      return

    clear = of.ofp_flow_mod(command=of.OFPFC_DELETE)
    self.connection.send(clear)
    self.connection.send(of.ofp_barrier_request())

    # From DHCPD
    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match()
    msg.match.dl_type = pkt.ethernet.IP_TYPE
    msg.match.nw_proto = pkt.ipv4.UDP_PROTOCOL
    #msg.match.nw_dst = IP_BROADCAST
    msg.match.tp_src = pkt.dhcp.CLIENT_PORT
    msg.match.tp_dst = pkt.dhcp.SERVER_PORT
    msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
    #msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
    self.connection.send(msg)

    core.openflow_discovery.install_flow(self.connection)

    src = self
    for dst in switches_by_dpid.itervalues():
      if dst is src: continue
      paths = _get_paths(src, dst)
      p = paths[0]
      if p is None or len(p) == 0: continue

      log.debug("Found a path: " + str(p))
      msg = of.ofp_flow_mod()
      msg.match = of.ofp_match()
      msg.match.dl_type = pkt.ethernet.IP_TYPE
      #msg.match.nw_dst = "%s/%s" % (dst.network, dst.subnet)
      msg.match.nw_dst = "%s/%s" % (dst.network, "255.255.0.0")

      msg.actions.append(of.ofp_action_output(port=p[0][1]))
      self.connection.send(msg)

      counter = 0
      for p in paths[1:]:
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match()
        msg.match.dl_type = pkt.ethernet.IP_TYPE
        msg.match.nw_proto = pkt.ipv4.TCP_PROTOCOL
        msg.match.tp_src = 5000 + counter
        #msg.match.nw_dst = "%s/%s" % (dst.network, dst.subnet)
        msg.match.nw_dst = "%s/%s" % (dst.network, "255.255.0.0")

        msg.actions.append(of.ofp_action_output(port=p[0][1]))
        self.connection.send(msg)
        counter += 1

    """
    # Can just do this instead of MAC learning if you run arp_responder...
    for port in self.ports:
      p = port.port_no
      if p < 0 or p >= of.OFPP_MAX: continue
      msg = of.ofp_flow_mod()
      msg.match = of.ofp_match()
      msg.match.dl_type = pkt.ethernet.IP_TYPE
      msg.match.nw_dst = "10.%s.%s.0/255.255.255.0" % (self._id,p)
      msg.actions.append(of.ofp_action_output(port=p))
      self.connection.send(msg)
    """

    for ip,mac in self.ip_to_mac.iteritems():
      self._send_rewrite_rule(ip, mac)

    flood_ports = []
    for port in self.ports:
      p = port.port_no
      if p < 0 or p >= of.OFPP_MAX: continue

      if core.openflow_discovery.is_edge_port(self.dpid, p):
        flood_ports.append(p)

      msg = of.ofp_flow_mod()
      msg.priority -= 1
      msg.match = of.ofp_match()
      msg.match.dl_type = pkt.ethernet.IP_TYPE
      msg.match.nw_dst = "10.%s.%s.0/255.255.255.0" % (self._id,p)
      msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
      self.connection.send(msg)

    msg = of.ofp_flow_mod()
    msg.priority -= 1
    msg.match = of.ofp_match()
    msg.match.dl_type = pkt.ethernet.IP_TYPE
    msg.match.nw_dst = "255.255.255.255"
    for p in flood_ports:
      msg.actions.append(of.ofp_action_output(port=p))
    self.connection.send(msg)


  def _send_rewrite_rule (self, ip, mac):
    p = ipinfo(ip)[1]

    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match()
    msg.match.dl_type = pkt.ethernet.IP_TYPE
    msg.match.nw_dst = ip
    msg.actions.append(of.ofp_action_dl_addr.set_src(self.mac))
    msg.actions.append(of.ofp_action_dl_addr.set_dst(mac))
    msg.actions.append(of.ofp_action_output(port=p))
    self.connection.send(msg)


  def disconnect (self):
    if self.connection is not None:
      log.debug("Disconnect %s" % (self.connection,))
      self.connection.removeListeners(self._listeners)
      self.connection = None
      self._listeners = None


  def connect (self, connection):
    if connection is None:
      self.log.warn("Can't connect to nothing")
      return
    if self.dpid is None:
      self.dpid = connection.dpid
    assert self.dpid == connection.dpid
    if self.ports is None:
      self.ports = connection.features.ports
    self.disconnect()
    self.connection = connection
    self._listeners = self.listenTo(connection)
    self._connected_at = time.time()

    label = dpid_to_str(connection.dpid)
    self.log = log.getChild(label)
    self.log.debug("Connect %s" % (connection,))

    if self._id is None:
      if self.dpid not in switches_by_id and self.dpid <= 254:
        self._id = self.dpid
      else:
        self._id = TopoSwitch._next_id
        TopoSwitch._next_id += 1
      switches_by_id[self._id] = self

    self.network = IPAddr("10.%s.0.0" % (self._id,))
    self.mac = dpid_to_mac(self.dpid)

    # Disable flooding
    con = connection
    log.debug("Disabling flooding for %i ports", len(con.ports))
    for p in con.ports.itervalues():
      if p.port_no >= of.OFPP_MAX: continue
      pm = of.ofp_port_mod(port_no=p.port_no,
                          hw_addr=p.hw_addr,
                          config = of.OFPPC_NO_FLOOD,
                          mask = of.OFPPC_NO_FLOOD)
      con.send(pm)
    con.send(of.ofp_barrier_request())
    con.send(of.ofp_features_request())

    # Some of this is copied from DHCPD's __init__().
    self.send_table()

    def fix_addr (addr, backup):
      if addr is None: return None
      if addr is (): return IPAddr(backup)
      return IPAddr(addr)

    self.ip_addr = IPAddr("10.%s.0.1" % (self._id,))
    #self.router_addr = self.ip_addr
    self.router_addr = None
    self.dns_addr = None #fix_addr(dns_address, self.router_addr)

    self.subnet = IPAddr("255.0.0.0")
    self.pools = {}
    for p in connection.ports:
      if p < 0 or p >= of.OFPP_MAX: continue
      self.pools[p] = [IPAddr("10.%s.%s.%s" % (self._id,p,n))
                       for n in range(1,255)]

    self.lease_time = 60 * 60 # An hour
    #TODO: Actually make them expire :)

    self.offers = {} # Eth -> IP we offered
    self.leases = {} # Eth -> IP we leased


  def _get_pool (self, event):
    pool = self.pools.get(event.port)
    if pool is None:
      log.warn("No IP pool for port %s", event.port)
    return pool


  def _handle_ConnectionDown (self, event):
    self.disconnect()


  def _mac_learn (self, mac, ip):
    if ip.inNetwork(self.network,"255.255.0.0"):
      if self.ip_to_mac.get(ip) != mac:
        self.ip_to_mac[ip] = mac
        self._send_rewrite_rule(ip, mac)
        return True
    return False


  def _on_lease (self, event):
    if self._mac_learn(event.host_mac, event.ip):
        self.log.debug("Learn %s -> %s by DHCP Lease",event.ip,event.host_mac)


  def _handle_PacketIn (self, event):
    packet = event.parsed
    arpp = packet.find('arp')
    if arpp is not None:
      if event.port != ipinfo(arpp.protosrc)[1]:
        self.log.warn("%s has incorrect IP %s", arpp.hwsrc, arpp.protosrc)
        return

      if self._mac_learn(packet.src, arpp.protosrc):
        self.log.debug("Learn %s -> %s by ARP",arpp.protosrc,packet.src)
    else:
      ipp = packet.find('ipv4')
      if ipp is not None:
        # Should be destined for this switch with unknown MAC
        # Send an ARP
        sw,p,_= ipinfo(ipp.dstip)
        if sw is self:
          log.debug("Need MAC for %s", ipp.dstip)
          core.ARPHelper.send_arp_request(event.connection,ipp.dstip,port=p)

    return super(TopoSwitch,self)._handle_PacketIn(event)


class topo_addressing (object):
  def __init__ (self):
    core.listen_to_dependencies(self, listen_args={'openflow':{'priority':0}})

  def _handle_ARPHelper_ARPRequest (self, event):
    pass # Just here to make sure we load it

  def _handle_openflow_discovery_LinkEvent (self, event):
    def flip (link):
      return Discovery.Link(link[2],link[3], link[0],link[1])

    l = event.link
    sw1 = switches_by_dpid[l.dpid1]
    sw2 = switches_by_dpid[l.dpid2]

    # Invalidate all flows and path info.
    # For link adds, this makes sure that if a new link leads to an
    # improved path, we use it.
    # For link removals, this makes sure that we don't use a
    # path that may have been broken.
    #NOTE: This could be radically improved! (e.g., not *ALL* paths break)
    clear = of.ofp_flow_mod(command=of.OFPFC_DELETE)
    for sw in switches_by_dpid.itervalues():
      if sw.connection is None: continue
      sw.connection.send(clear)
    path_map.clear()

    if event.removed:
      # This link no longer okay
      if sw2 in adjacency[sw1]: del adjacency[sw1][sw2]
      if sw1 in adjacency[sw2]: del adjacency[sw2][sw1]

      # But maybe there's another way to connect these...
      for ll in core.openflow_discovery.adjacency:
        if ll.dpid1 == l.dpid1 and ll.dpid2 == l.dpid2:
          if flip(ll) in core.openflow_discovery.adjacency:
            # Yup, link goes both ways
            log.debug("Adjacency: " + str(sw1) + " " + str(sw2))
            adjacency[sw1][sw2] = ll.port1
            adjacency[sw2][sw1] = ll.port2
            # Fixed -- new link chosen to connect these
            break
    else:
      # If we already consider these nodes connected, we can
      # ignore this link up.
      # Otherwise, we might be interested...
      if adjacency[sw1][sw2] is None:
        # These previously weren't connected.  If the link
        # exists in both directions, we consider them connected now.
        if flip(l) in core.openflow_discovery.adjacency:
          # Yup, link goes both ways -- connected!
          log.debug("Adjacency: " + str(sw1) + " " + str(sw2))
          adjacency[sw1][sw2] = l.port1
          adjacency[sw2][sw1] = l.port2

    for sw in switches_by_dpid.itervalues():
      sw.send_table()


  def _handle_openflow_ConnectionUp (self, event):
    sw = switches_by_dpid.get(event.dpid)

    if sw is None:
      # New switch

      sw = TopoSwitch()
      switches_by_dpid[event.dpid] = sw
      sw.connect(event.connection)
    else:
      sw.connect(event.connection)



def launch (debug = False):
  core.registerNew(topo_addressing)
  from proto.arp_helper import launch
  launch(eat_packets=False)
  # Normally 360
  core.callDelayed(180, compute_paths)
  if not debug:
    core.getLogger("proto.arp_helper").setLevel(99)

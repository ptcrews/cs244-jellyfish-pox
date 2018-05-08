import os
import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from subprocess import Popen
from time import sleep, time
import random
from random import shuffle
from threading import Timer

from construct_paths import Paths

ip_dict = {}

class JellyFishTop(Topo):

    k = 15#Ports per switch #24
    r = 5#Ports dedicated to connecting to other ToR switches #10
    num_switches = 20#49

    def portListContainsOther(self, port, portList):
        for x in portList:
            if x != port:
                return True
        return False

    def build(self):

        hostList = []
        switchList = []
        portList = []


        #Add all switches to the topology
        counter = 0
        for y in range(self.num_switches):
            switchList.append(self.addSwitch('s%s' % (y)))
            for j in range(self.k-self.r):
                host_name = 'h' + str(counter)
                switch_num_str = str(y)
                if y == 0: switch_num_str = "100"
                ip_dict[host_name] = "10." + switch_num_str + "." + str(j+1) + ".1"
                host = self.addHost(host_name, ip='0.0.0.0')
                hostList.append(host)
                self.addLink(switchList[y], hostList[-1], bw=10)
                counter += 1
            for x in range(self.r):
                portList.append(y)

        for currentSwitch in range(self.num_switches):

            canConnect = []
            for z in range(len(switchList)):
                is_neighbor = False
                for link in self.links():
                    if switchList[z] in link and switchList[currentSwitch] in link:
                        is_neighbor = True
                        break

                if not is_neighbor and z in portList and z != currentSwitch:
                    canConnect.append(z)

            while currentSwitch in portList and len(canConnect) > 0:
                if len(canConnect) == 1:
                    randNum = 0
                else:
                    randNum = random.randint(0, len(canConnect)-1)

                randPort = canConnect[randNum]

                portList.remove(randPort)
                portList.remove(currentSwitch)
                canConnect.remove(randPort)
                self.addLink(switchList[currentSwitch], switchList[randPort], bw=100)

        for x in self.links():
            print x

def experiment(net):
        net.start()
        sleep(20)
        net.pingAll()
        net.stop()

def test_timeout(net):
    print "Test timed out"
    net.stop()
    sleep(30)
    sys.exit()

def main():
    if "N_FLOWS" in os.environ:
        n_flows = int(os.environ["N_FLOWS"])
    else:
        n_flows = 1
    
    if "TEST_NAME" in os.environ:
        test_name = os.environ["TEST_NAME"]
    else:
        test_name = "KSP"

    if "TEST_NUM" in os.environ:
        test_num = int(os.environ["TEST_NUM"])
    else:
        test_num = 0

    topo = JellyFishTop()
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
    net.start()
    # NOTE: Must come after net.start
    sleep(30)
    for host in net.hosts:
        print str(host)
        print str(host.defaultIntf().name)
	host.cmdPrint('dhclient '+host.defaultIntf().name)
    sleep(60)
    host_list = []
    for host in net.hosts:
        host_list.append(host)
    shuffle(host_list)

    t = Timer(120.0, test_timeout, [net])
    t.start()

    for i in range(len(host_list)/2):
        host1 = host_list[i]
        host2 = host_list[len(host_list)/2 + i]
        dirname = "test_" + test_name + "_" + str(n_flows)
        outfile = dirname + "/" + str(test_num) + "_" + str(host1.name) + "_" + str(host2.name)
        host1.cmd('iperf3 -s -p 4500 &')
        if n_flows == 1:
            host2.sendCmd('iperf3 -p 4500 -c '+ ip_dict[host1.name] + ' -J > ' + outfile)
        else:
            host2.sendCmd('iperf3 -p 4500 -P 8 -c '+ ip_dict[host1.name] + ' --cport 5000 -J > ' + outfile)
    results = {}
    for i in range(len(host_list)/2):
        host = host_list[len(host_list)/2 + i]
        results[host.name] = host.waitOutput()
        print str(results[host.name])
    
    #CLI(net)
    net.stop()

if __name__ == "__main__":
    main()


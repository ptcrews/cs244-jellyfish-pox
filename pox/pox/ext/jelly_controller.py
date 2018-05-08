# Copyright 2012 James McCauley
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
Demonstrates the spanning tree module so that the L2 switch
works decently on topologies with loops.
"""

def launch ():
  import pox.log.color
  pox.log.color.launch()
  import pox.log
  pox.log.launch(format="[@@@bold@@@level%(name)-22s@@@reset] " +
                        "@@@bold%(message)s@@@normal")
  from pox.core import core
  import pox.openflow.discovery
  pox.openflow.discovery.launch(link_timeout='20')
  
  import pox.openflow.keepalive
  pox.openflow.keepalive.launch(interval='10000', timeout='10000')

  core.getLogger("openflow.spanning_tree").setLevel("INFO")

  import pox.ext.topo_proactive as fw
  core.getLogger().debug("Using forwarding: %s", fw.__name__)
  fw.launch()

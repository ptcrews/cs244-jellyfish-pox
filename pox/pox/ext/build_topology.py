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



class JellyFishTop(Topo):
    ''' TODO, build your topology here'''

    k = 24 #Ports per switch
    r = 10 #Ports dedicated to connecting to other ToR switches
    num_switches = 49

    def build(self):

        hostList = []
        switchList = []
        portList = []

        # Add all servers to the topology
        for x in range((k-r)*num_switches):

        #Add all switches to the topology
        for y in range(num_switches):
            switchList.append(self.addSwitch('s%s' % (y)))
            for j in range(k-r):
                hostList.append(self.addHost('switch' + str(y) + 'h' + str(x)))
                self.addLink(switchList[y], hostList.tail())
            for x in range(r):
                portList.append(y)

        while(len(portList) > 1):
            freeSwitch1 = portList[random.randint(0, len(portList))]

            currentNeighbors = []

            for link in self.links():
                if freeSwitch1 in link:
                    if link[0] != freeSwitch1:
                        currentNeighbors.append(link[0])
                    else:
                        currentNeighbors.append(link[1])

            #So now we have a neighbor list

                    

            randPort2 = portList[random.randint(0, len(portList))]
            if(randPort1 == randPort2):
                continue
            tupleToAdd = (switchList[randPort1], switchList[randPort2])
            tupleToAddReverse = (switchList[randPort2], switchList[randPort1])
            if(tupleToAdd in self.links() or tupleToAddReverse in self.links):
                continue
            
            self.addLink(switchList[randPort1],switchList[randPort2])
            portList.remove(randPort1)
            portList.remove(randPort2)
            

        #leftHost = self.addHost( 'h1' )
        #rightHost = self.addHost( 'h2' )
        #leftSwitch = self.addSwitch( 's3' )
        #rightSwitch = self.addSwitch( 's4' )

        # Add links
        #self.addLink( leftHost, leftSwitch )
        #self.addLink( leftSwitch, rightSwitch )
        #self.addLink( rightSwitch, rightHost )


def experiment(net):
        net.start()
        sleep(3)
        net.pingAll()
        net.stop()

def main():
	topo = JellyFishTop()
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
	experiment(net)

if __name__ == "__main__":
	main()


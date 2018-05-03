from collections import defaultdict
import matplotlib.pyplot as plt
import random
import copy

class Paths ():
    # Adjacency map.  [sw1][sw2] -> port from sw1 to sw2
    '''
    def __init__ (self, adjacency_map, switches_by_dpid):
        sws = switches_by_dpid.values()
        path_map.clear()
        for k in sws:
            for j,port in adjacency[k].iteritems():
                if port is None: continue
                path_map[k][j] = (1,None)
            path_map[k][k] = (0,None) # distance, intermediate
            '''


    # Simple source - to - dest Dijkstra implementation
    # switches = list of switch ids (e.g. switches_by_dpid.values())
    def dijkstra (self, switches, adjacency, source, dest):
        # List of all the switches by dpid
        # TODO: Should probably be a set...
        Q = copy.deepcopy(switches)

        dist = {}
        prev = {}

        for v in Q:
            dist[v] = float('Inf')
            prev[v] = None

        dist[source] = 0

        while len(Q) > 0:
            min_found = float('Inf')
            for u in Q:
                if dist[u] < min_found:
                    min_found = u

            # No path found
            if min_found == float('Inf'):
                return []

            Q.remove(min_found)
            if min_found == dest:
                break

            for v,port in adjacency[min_found].iteritems():
                if dist[min_found] + 1 < dist[v] and port != None:
                    dist[v] = dist[min_found] + 1
                    prev[v] = min_found

        path = []
        prev_node = dest
        path.insert(0, (prev_node, None))
        while prev_node in prev and prev[prev_node] != None:
            cur_node = prev[prev_node]
            path.insert(0, (cur_node, adjacency[cur_node][prev_node]))
            prev_node = cur_node

        if prev_node != source:
            return []

        return path

    def delete_node(self, adjacency, switches, node):
        for i in range(len(switches)):
            self.remove_edges(adjacency, node, i)

    def dump(self, adjacency):
        for node in adjacency:
            print "Node: " + str(node)
            for connected in adjacency[node]:
                print "\t Connected to " + str(connected) + " with value " + \
                    str(adjacency[node][connected])

    #def check_integrity

    def remove_edges(self, adjacency, first_node, second_node):
        if adjacency[first_node][second_node] != None:
            del adjacency[first_node][second_node]
        if adjacency[second_node][first_node] != None:
            del adjacency[second_node][first_node]

    def find_remove_min(self, path_list):
        if len(path_list) == 0:
            return None

        min_index = 0
        for i in range(len(path_list)):
            if len(path_list[i]) < len(path_list[min_index]):
                min_index = i
        res = path_list[i]
        del path_list[i]
        return res

    # This implementation now *kind of* works
    # Heavily inspired by the Wikipedia psuedo-code for Yen's K shortest paths
    # algorithm
    def yen_ksp(self, switches, adjacency, source, dest, K):
        A = []
        # Find the shortest path
        A.append(self.dijkstra(switches, adjacency, source, dest))
 #       print "Dijkstra result from " + str(source) + " to " + str(dest) + " is: " + str(A)
        B = []

        for k in range(1, K+1):
            for i in range(0, len(A[k-1])-1):
                adjacency_copy = copy.deepcopy(adjacency)
                spurNode = A[k-1][i] # Should retrieve i-th node

                rootPath = A[k-1][:i+1]

                for p in A:
                    if rootPath == p[:i+1]:
                        first_node = p[i][0]
                        second_node = p[i+1][0]
                        self.remove_edges(adjacency_copy, first_node, second_node)

                for node in rootPath:
                    if node == spurNode:
                        continue
                    self.delete_node(adjacency_copy, switches, node[0])

                spurPath = self.dijkstra(switches, adjacency_copy, spurNode[0], dest)
                if spurPath == []:
                    continue

                totalPath = rootPath + spurPath[1:]
                B.append(totalPath)

                # Restore edges to graph... :/

            if len(B) == 0:
                break

            A.append(self.find_remove_min(B))

        return A

    def all_k_shortest_paths (self, switches, adjacency, K):
        path_map = defaultdict(lambda:defaultdict(lambda:(None,None)))
        for i in switches:
            for j in switches:
                res = self.yen_ksp(switches, adjacency, i, j, K)
                path_map[i][j] = res
                print "Paths from " + str(i) + " to " + str(j) + " : " + str(res)

    def ecmp (self, switches, adjacency, src, dst, K):
        ksp = self.yen_ksp(switches, adjacency, src, dst, K)
        print "ksp before sort: " + str(ksp)
        ksp.sort(key=len)
        print "ksp after sort: " + str(ksp)
        shortest_path_length = len(ksp[0])
        print "shortest length path is: " + str(shortest_path_length)
        for path in ksp:
            if len(path) > shortest_path_length:
                ksp.remove(path)

        return ksp

    def simple_test (self):
        switches = [0, 1, 2, 3, 4]
        n_ports = 2
        adjacency = defaultdict(lambda:defaultdict(lambda:(None,None)))
        # Simple tree topology
        adjacency[0][1] = 0
        adjacency[1][0] = 0

        adjacency[0][2] = 1
        adjacency[2][0] = 1

        adjacency[1][3] = 1
        adjacency[3][1] = 1

        adjacency[2][4] = 1
        adjacency[4][2] = 1

        adjacency[0][4] = 1
        adjacency[4][0] = 1

#        res = self.yen_ksp(switches, adjacency, 3, 4, 2)
#        ecmp_res = self.ecmp(switches, adjacency, 3, 4, 2)
#        print "K shortest paths: " + str(res)
#        print "ECMP-2: " + str(ecmp_res)
        ksp_res = self.count_distinct_paths(adjacency, switches, 2, 0, None)
        ecmp8_res = self.count_distinct_paths(adjacency, switches, 2, 1, ksp_res[1])
        ecmp64_res = self.count_distinct_paths(adjacency, switches, 2, 2, ksp_res[1])


        print "KSP Result: " + str(ksp_res[0])
        print "ECMP-8 Result: " + str(ecmp8_res[0])
        print "ECMP-64 Result: " + str(ecmp64_res[0])

        self.plot_results(ksp_res[0], ecmp8_res[0], ecmp64_res[0])
        
        #self.all_k_shortest_paths(switches, adjacency, 2)



    def count_distinct_paths(self, adjacency, switches, hosts_per_switch, mode, serverPairs): #mode 0= KSP-8, mode 1=ECMP-8, mode 2=ECMP-64
        #Pass serverPairs if you want to rerun this method with the same traffic permutation as a previous run

        hosts= []

#        print "Switch count in count_paths is: " + str(len(switches))

        for switchNum in switches:
            for j in range (0, hosts_per_switch):
                hosts.append(switchNum)

        #Now hosts is a list containing each switch number hosts_per_switch times

        distinct_path_count = copy.deepcopy(adjacency)

        #set all elements in this adjacency copy to 0
    #    print "len(dist_path_count is: " + str(len(distinct_path_count))
        for i in distinct_path_count:
#            print "len(dist_path_count[i]) is : " + str(len(distinct_path_count[i]))
            for j in distinct_path_count[i]:
                distinct_path_count[i][j] = 0
   #             print "Storing " + str(distinct_path_count[i][j]) + " in spot " + str(i) + "," + str(j)

        unmatchedServers = []
        if serverPairs is None: #Need to generate new traffic permutation
            serverPairs = [] #List of tuples where each tuple is a pair of servers

            unmatchedServers = copy.copy(hosts) #this is a list containing all servers which have not been paired with another random server


        while len(unmatchedServers) > 0: #Pair each server with another random, as of yet unpaired server
            if len(unmatchedServers) == 1:
                    print "Error - odd number of remaining servers"
                    break
            rand1 = random.randint(0, len(unmatchedServers) - 1)
            rand2 = random.randint(0, len(unmatchedServers) - 1)
            while rand2 == rand1:
                rand2 = random.randint(0, len(unmatchedServers) - 1)
  #          print "Rand1 is: " + str(rand1) + " and len(unamatched) is " + str(len(unmatchedServers)) 
            randServ1 = unmatchedServers[rand1]
            randServ2 = unmatchedServers[rand2]
            serverPairs.append((randServ1, randServ2))
            unmatchedServers.remove(randServ1)
            unmatchedServers.remove(randServ2)

        # Now all servers have been paired

        # HostToSwitchPathCount = []


        for pairing in serverPairs: #Run KSP for each pairing
            if mode == 0:
                paths = self.yen_ksp(switches, adjacency, pairing[0], pairing[1], 8) #KSP-8
            elif mode == 1:
                paths = self.ecmp(switches, adjacency, pairing[0], pairing[1], 8) #ECMP-8
            elif mode == 2:
                paths = self.ecmp(switches, adjacency, pairing[0], pairing[1], 64) #ECMP-64
            print "Evaluating Pairing from " + str(pairing[0]) + " to " + str(pairing[1])
            #HostToSwitchPathCount.append(0)
            #HostToSwitchPathCount.append(0)

            for path in paths: #Iterate through each link in each path and increment accordingly
                for nodeIndex in range(0, len(path)): 
                    if nodeIndex < len(path) - 1: #Not the last node
                        node1 = path[nodeIndex][0]
                        node2 = path[nodeIndex + 1][0]
                        #Link is represented as the connection of these two nodes in adjacency matrix
                        #Increment count for both directions of this link, as done for figure 9
 #                       print "Host1 in this link: " + str(node1) + " Host2 in this link: " + str(node2) + " Current number of other distinct paths that have traversed this link: " + str(distinct_path_count[node1][node2]) + " which should be equal to " + str(distinct_path_count[node2][node1])
                        
                        distinct_path_count[node1][node2] += 1
                        distinct_path_count[node2][node1] += 1

                        if distinct_path_count[node2][node1] !=  distinct_path_count[node1][node2]:
                            print "ERROR - some link was not counted in both directions: 1,2 gives: " + str(distinct_path_count[node1][node2]) + " while 2,1 gives: " + str(distinct_path_count[node2][node1])

            
                        #print "AFTER INCREMENT Host1 in this link: " + str(node1) + " Host2 in this link: " + str(node2) + " Current number of other distinct paths that have traversed this link: " + str(distinct_path_count[node1][node2])
        #Finished calculating for all links between switches. However, the design of yen_ksp
        # means that links from host -> switch have not yet been considered. Im not sure if I
        # should be counting those anyway

        #Convert this matrix into an ordered ranking of links that exist (requires comparing against adjacency)

        pathCountList = [] #List of all pathCounts

        for i in adjacency:
            for j in adjacency[i]:
                if adjacency[i][j] is not None:
                    pathCountList.append(distinct_path_count[i][j])
                    print "Link from switch " + str(i) + " to " + str(j) + " is on " + str(distinct_path_count[i][j]) + " distinct paths." 
                elif distinct_path_count[i][j] is not None:
                    print "ERROR: COunted on link where none should exist"
                else:
                    print "ERROR: found none in adj matrix"

        pathCountList.sort() #Modifies pathCountList


        return (pathCountList, serverPairs)

    def plot_results(self, ksp_res, ecmp8_res, ecmp64_res):

        ksp_line = plt.plot(ksp_res, label='8 Shortest Paths')
        ecmp8_line = plt.plot(ecmp8_res, label='8-Way ECMP')
        ecmp64_line = plt.plot(ecmp64_res, label='64-Way ECMP')
        plt.legend()
        plt.ylabel('# Distinct Paths Link is on')
        plt.xlabel('Rank of Link')
        plt.grid()
        plt.show()

if __name__ == "__main__":
    paths = Paths()
    paths.simple_test()

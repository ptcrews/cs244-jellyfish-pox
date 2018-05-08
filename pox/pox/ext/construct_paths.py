from collections import defaultdict
import matplotlib.pyplot as plt
import random
import copy
import ast

K_VAL = 8

KSP_MODE = 0
ECMP8_MODE = 1
ECMP64_MODE = 2
MODE = KSP_MODE

MODE = KSP_MODE
class Paths ():
    adjacency = defaultdict(lambda:defaultdict(lambda:(None,None)))
    path_map = defaultdict(lambda:defaultdict(lambda:(None,None)))
    switches_by_dpid = []
    # Adjacency map.  [sw1][sw2] -> port from sw1 to sw2
    def __init__ (self, topo=None):
        self.adjacency.clear()
        self.path_map.clear()

        if topo == None:
            return

        for switch in topo.switches:
            self.switches_by_dpid.append(switch.dpid)

        for link in topo.links:
            first_node = link.intf1.node
            second_node = link.intf2.node
            if first_node in topo.switches and second_node in topo.switches:
                first_dpid = first_node.dpid
                second_dpid = second_node.dpid
                self.adjacency[first_dpid][second_dpid] = 1
                self.adjacency[second_dpid][first_dpid] = 1

    def get_paths(self, path_map, switchlist, adjacency, src, dst):
        # Recomptues all paths if path_map is empty
        if len(path_map) == 0:
            self.compute_all_paths(path_map, switchlist, adjacency)
        return path_map[src][dst]


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
            min_found = None
            for u in Q:
                if min_found == None or dist[u] < dist[min_found]:
                    min_found = u

            # No path found
            if min_found == float('Inf'):
                return []

            Q.remove(min_found)

            for v in adjacency[min_found]:
                port = adjacency[min_found][v]
                if dist[min_found] + 1 < dist[v]:
                    dist[v] = dist[min_found] + 1
                    prev[v] = min_found

            if min_found == dest:
                break

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
        for i in switches:
            self.remove_edges(adjacency, node, i)

    def dump(self, adjacency):
        for node in adjacency:
            for connected in adjacency[node]:
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

        for k in range(1, K):
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

    def compute_all_paths (self, path_map, switches, adjacency):
        path_map.clear()
        for i in switches:
            for j in switches:
                if MODE == KSP_MODE:
                    res = self.yen_ksp(switches, adjacency, i, j, K_VAL)
                elif MODE == ECMP8_MODE:
                    res = self.ecmp(switches, adjacency, i, j, 8)
                else: # MODE == ECMP64_MODE
                    res = self.ecmp(switches, adjacency, i, j, 64)
                path_map[i][j] = res

    def ecmp (self, switches, adjacency, src, dst, K):
        ksp = self.yen_ksp(switches, adjacency, src, dst, K)
        '''ksp8 = self.yen_ksp(switches, adjacency, src, dst, 8)
        print "KSP8 is: " + str(ksp8)
        ksp64 = self.yen_ksp(switches, adjacency, src, dst, 64)
        quit = 0
        if len(ksp64) < len(ksp8):
            print "ERROR!! KSP8 found more paths"
            quit = 1
        for path in ksp8:
            path_in_ksp64 = 0
            for path64 in ksp64:
                if path64 == path:
                    print "match"
                    path_in_ksp64 = 1
                    break
            print "hi"
            if path_in_ksp64 == 0:
                print "ERROR: path: " + str(path) + " is in ksp8 but not ksp64"
                exit()
        print "KSP64 is: " + str(ksp64)
        print "ksp before sort: " + str(ksp)'''
        ksp.sort(key=len)
        '''        ksp64.sort(key=len)
        ksp8.sort(key=len)
        print "ksp after sort: " + str(ksp)'''
        shortest_path_length = len(ksp[0])
        print "shortest_path_length is: " + str(len(ksp[0]))
        '''        print "shortest length path ksp8 is: " + str(len(ksp8[0]))
        print "shortest length path ksp64 is: " + str(len(ksp64[0]))
        if quit == 1:
            exit()
            while(1):
                print "FAILURE"'''

        print "Number of paths found before pruning: " + str(len(ksp))
        return_paths=[]

        for path in ksp:
            if len(path) == shortest_path_length:
                return_paths.append(path)

        print "Paths remaining after pruning" + str(len(return_paths))

        '''        for path in ksp8:
            if len(path) > len(ksp8[0]):
                ksp8.remove(path)
        for path in ksp64:
            if len(path) > len(ksp64[0]):
                ksp64.remove(path)
        if(len(ksp8) > len(ksp64)):
            print "ERROR NUMBER 2"
            exit()'''
        return return_paths

    def simple_test (self):
        switches = [0, 1, 2, 3, 4, 5, 6, 7]
        n_ports = 3
        hosts_per_switch = 24
        adjacency = defaultdict(lambda:defaultdict(lambda:(None,None)))
        # Simple tree topology
        self.adjacency[0][1] = 0
        self.adjacency[1][0] = 0

        self.adjacency[0][2] = 1
        self.adjacency[2][0] = 1

        self.adjacency[1][3] = 1
        self.adjacency[3][1] = 1

        self.adjacency[2][4] = 1
        self.adjacency[4][2] = 1

        adjacency[1][7] = 1
        adjacency[7][1] = 1

        adjacency[7][4] = 1
        adjacency[4][7] = 1

        adjacency[6][4] = 1
        adjacency[4][6] = 1

        adjacency[7][5] = 1
        adjacency[5][7] = 1

        adjacency[5][6] = 0
        adjacency[6][5] = 0

        adjacency[5][0] = 2
        adjacency[0][5] = 2


#        res = self.yen_ksp(switches, adjacency, 3, 4, 2)
#        ecmp_res = self.ecmp(switches, adjacency, 3, 4, 2)
#        print "K shortest paths: " + str(res)
#        print "ECMP-2: " + str(ecmp_res)
        '''        adjacency2 = copy.deepcopy(adjacency)
        adjacency3 = copy.deepcopy(adjacency)
        switches2 = copy.deepcopy(switches)
        switches3 = copy.deepcopy(switches)
        ksp_res = self.count_distinct_paths(adjacency, switches, hosts_per_switch, KSP_MODE, None)
        ecmp8_res = self.count_distinct_paths(adjacency2, switches2, hosts_per_switch, ECMP8_MODE, ksp_res[1])
        ecmp64_res = self.count_distinct_paths(adjacency3, switches3, hosts_per_switch, ECMP64_MODE, ksp_res[1])


        print "KSP Result: " + str(ksp_res[0])
        print "ECMP-8 Result: " + str(ecmp8_res[0])
        print "ECMP-64 Result: " + str(ecmp64_res[0]) '''


#        self.plot_results(ksp_res[0], ecmp8_res[0], ecmp64_res[0])

        #ksp_string = u'[0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 16, 17, 17, 17, 17, 17, 17, 17, 17, 18, 18, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 20, 20, 20, 20, 22, 22, 23, 23, 23, 23, 23, 23, 23, 23, 26, 26, 27, 27, 27, 27]'
        
        #ecmp8_string = u'[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 9, 9, 9, 9]'

        #ecmp64_string = u'[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 9, 9, 9, 9]'
        kspfile = open("ksp8_res.txt", "r")
        ksp_string = kspfile.read()
        kspfile.close()
        ksp_string_res = ast.literal_eval(ksp_string)
        ecmp8file = open("ecmp8_res.txt", "r")
        ecmp8_string = ecmp8file.read()
        ecmp8file.close()
        ecmp8_string_res = ast.literal_eval(ecmp8_string)
        ecmp64file = open("ecmp64_res.txt", "r")
        ecmp64_string = ecmp64file.read()
        ecmp64file.close()
        ecmp64_string_res = ast.literal_eval(ecmp64_string)

        self.plot_results(ksp_string_res, ecmp8_string_res, ecmp64_string_res)        
        #self.all_k_shortest_paths(switches, adjacency, 2)



    def count_distinct_paths(self, hosts_per_switch, mode, serverPairs): #mode 0= KSP-8, mode 1=ECMP-8, mode 2=ECMP-64
        #Pass serverPairs if you want to rerun this method with the same traffic permutation as a previous run
        adjacency = self.adjacency
        switches = self.switches_by_dpid
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
            
            #Begin mod to only pick one valid path per pairing (at random!)

            rand3 = random.randint(0, len(paths) - 1)
            path = paths[rand3]

            #for path in paths: #Iterate through each link in each path and increment accordingly
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
        print "In plot_results"
        print "ksp_res is: " + str(ksp_res)
        ksp_line = plt.plot(ksp_res, label='8 Shortest Paths')
        print "KSP-8 plotted"
        ecmp8_line = plt.plot(ecmp8_res, label='8-Way ECMP')
        ecmp64_line = plt.plot(ecmp64_res, label='64-Way ECMP')
        print "Plotting complete, showing soon"
        plt.legend(loc=2)
        plt.ylabel('# Distinct Paths Link is on')
        plt.xlabel('Rank of Link')
        plt.grid()
        plt.show()
        print "Plot.show called"

if __name__ == "__main__":
    paths = Paths()
    paths.simple_test()

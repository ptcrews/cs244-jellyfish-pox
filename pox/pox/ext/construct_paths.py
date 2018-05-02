from collections import defaultdict
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
        print "Dijkstra result from " + str(source) + " to " + str(dest) + " is: " + str(A)
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

    def simple_test (self):
        switches = [0, 1, 2, 3, 4]
        n_ports = 2
        adjacency = defaultdict(lambda:defaultdict(lambda:(None,None)))
        # Simple tree topology
        adjacency[0][1] = 0
        adjacency[1][0] = 0

        adjacency[0][2] = 1
        adjacency[2][0] = 1

        adjacency[1][0] = 0
        adjacency[0][1] = 0

        adjacency[1][3] = 1
        adjacency[3][1] = 1

        adjacency[2][0] = 0
        adjacency[0][2] = 0

        adjacency[2][4] = 1
        adjacency[4][2] = 1

        adjacency[3][1] = 0
        adjacency[1][3] = 0

        adjacency[4][2] = 0
        adjacency[2][4] = 0

        adjacency[3][4] = 1
        adjacency[4][3] = 1

        res = self.yen_ksp(switches, adjacency, 3, 4, 2)
        print "K shortest paths: " + str(res)
        self.all_k_shortest_paths(switches, adjacency, 2)

    def count_distinct_paths(self, adjacency, switches, hosts):
        distinct_path_count = copy.deepcopy(adjacency)

        #set all elements in this adjacency copy to 0
        for i in len(distinct_path_count):
            for j in len(distinct_path_count[i]):
                distinct_path_count[i][j] = 0

        unmatchedServers = copy(hosts) #this is a list containing all servers which have not been paired with another random server
        serverPairs = [] #List of tuples where each tuple is a pair of servers

        while len(unmatchedServers) > 0: #Pair each server with another random, as of yet unpaired server
            rand1 = random.randint(0, len(unmatchedServers))
            rand2 = random.randint(0, len(unmatchedServers))
            while rand2 == randServ1:
                rand2 = random.randint(0, len(unmatchedServers))
        
            randServ1 = unmatchedServers[rand1]
            randServ2 = unmatchedServers[rand2]
            serverPairs.append((randServ1, randServ2))
            unmatchedServers.remove(randServ1)
            unmatchedServers.remove(randServ2)

        #Now all servers have been paired

        for pairing in serverPairs: #Run KSP for each pairing
            paths = self.yen_ksp(switches, adjacency, pairing[0], pairing[1], 8) #KSP-8
            for path in paths: #Iterate through each link in each path and increment accordingly
                for nodeIndex in range(0, len(path)): 
                    if nodeIndex < len(path) - 1: #Not the last node
                        node1 = path[nodeIndex]
                        node2 = path[nodeIndex + 1]
                        #Link is represented as the connection of these two nodes in adjacency matrix
                        #Increment count for both directions of this link, as done for figure 9
                        distinct_path_count[node1][node2] += 1
                        distinct_path_count[node2][node1] += 1
            
        #Finished!

        #Convert this matrix into an ordered ranking of links that exist (requires comparing against adjacency)

        pathCountList = [] #List of all pathCounts

        for i in len(adjacency)
            for j in len(adjacency[i])
                if adjacency[i][j] == 1:
                    pathCountList.append(distinct_path_count[i][j])

        pathCountList.sort() #Modifies pathCountList

        return distinct_path_count


if __name__ == "__main__":
    paths = Paths()
    paths.simple_test()

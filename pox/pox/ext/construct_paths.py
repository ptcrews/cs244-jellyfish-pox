from collections import defaultdict
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

if __name__ == "__main__":
    paths = Paths()
    paths.simple_test()

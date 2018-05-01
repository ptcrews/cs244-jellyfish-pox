from collections import defaultdict

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
        Q = switches

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

            Q.remove(min_found)
            if min_found == dest:
                break

            for v,port in adjacency[min_found].iteritems():
                if dist[min_found] + 1 < dist[v]:
                    dist[v] = dist[min_found] + 1
                    prev[v] = min_found

        path = []
        u = dest
        while prev[u] != None:
            # Push the next hop id and port
            # Note that this link *must* exist in the adjacency graph
            # TODO: Deeply consider whether to have the (node, port_to_get_to_node)
            # or (node, egress_port) as the tuple
            path.insert(0, (u, adjacency[prev[u]][u]))
            u = prev[u]
        # Finally push ourselves and no port?
        path.insert(0, (u, None))

        return path

    # TODO: Many, numerous, incalcuable problems with all of this :/
    def yen_ksp(switches, adjacency, source, dest, K):
        A = []
        # Find the shortest path
        A.append(dijkstra(switches, adjacency, source, dest))

        B = {}

        # TODO: Off by one?
        for k in range(1..K):
            for i in range(len(A[k-1])-1):
                spurNode = A[k-1][i][0] # Should retrieve i-th node

                rootPath = A[k-1][0..i]

                for p in A:
                    if rootPath == p[0..i]:
                        # TODO: Confirm removal here is correct
                        adjacency[p[i]][p[i+1]] = None

                for node in rootPath:
                    if node != spurNode:
                        continue
                    # TODO: how to remove node from graph?? just invalidate edges?
                    # remove node from Graph

                spurPath = dijkstra(switches, adjacency, spurNode, dest)

                totalPath = rootPath + spurPath
                B.append(totalPath)

                # Restore edges to graph... :/

            if len(B) == 0:
                break

            B.sort()
            A[k] = B[0]
            B.pop()

        return A

    def simple_test (self):
        switches = [0, 1, 2, 3, 4]
        n_ports = 2
        adjacency = defaultdict(lambda:defaultdict(lambda:(None,None)))
        # Simple tree topology
        adjacency[0][1] = 0
        adjacency[0][2] = 1
        adjacency[1][0] = 0
        adjacency[1][3] = 1
        adjacency[2][0] = 0
        adjacency[2][4] = 1
        adjacency[3][1] = 0
        adjacency[4][2] = 0
        print str(self.dijkstra(switches, adjacency, 3, 4))

if __name__ == "__main__":
    paths = Paths()
    paths.simple_test()

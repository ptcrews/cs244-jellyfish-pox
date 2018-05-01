# [sw1][sw2] -> (distance, intermediate)
#path_map = defaultdict(lambda:defaultdict(lambda:(None,None)))
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


    # Simple breadth first search
    def dijkstra (self, adjacency, source, dest):
        # List of all the switches by dpid
        Q = switches_by_dpid.values()

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
            path.insert(0, u)
            u = prev[u]
        path.insert(0, u)

        return path

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
        print str(self.dijkstra(adjacency, 3, 4))

if __name__ == "__main__":
    paths = Paths()
    paths.simple_test()

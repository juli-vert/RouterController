import json
class graph:

    def __init__(self):
        self.g = {}
        self.fullroute = None

    def listofvertex(self):
        return self.g.keys()

    def vertexexists(self, vname):
        return vname in self.g.keys()

    def addvertex(self, v):
        if v.name not in self.g.keys():
            self.g.update({v.name:v})
            self.printgraph()
            print('!--- New vertex found: Updating routing tables ---!')
            self.fullroute = self.fullDijkstra()
            for v in self.g.keys(): #send the vertex routes to each
                self.g[v].updaterouting(self.fullroute[v])
            return 1
        else:
            print("Vertex {0} is already in the graph".format(v.name))
            return 0

    def delvertex(self, v):
        if v.name not in self.g.keys():
            print("Vertex {0} is not in the graph".format(v.name))
        else:
            print("Recalculating routes: Convergency in progress")
            for ver in self.g.keys():
                self.g[ver].delneighbor(self.g[v.name])
            del self.g[v.name]
            self.fullroute = self.fullDijkstra()
            for v in self.g.keys(): #send the vertex routes to each
                self.g[v].updaterouting(self.fullroute[v])

    # to be changed. Currently it's bidirectional with equal cost, it must
    # be defined by direction
    def addedge(self, vs, vd, cost1, cost2, via):
        if vs != vd:
            self.g[vs.name].addneighbor(self.g[vd.name], cost1, via)
            self.g[vd.name].addneighbor(self.g[vs.name], cost2, via)
            self.printgraph()
            print('!--- New adjacency found: Updating routing tables ---!')
            self.fullroute = self.fullDijkstra()
            for v in self.g.keys(): #send the vertex routes to each
                self.g[v].updaterouting(self.fullroute[v])
            return 1
        else:
            return 0

    def deledge(self, vs, vd):
        if self.g[vs.name].delneighbor(self.g[vd.name]) and self.g[vd.name].delneighbor(self.g[vs.name]):
            self.printgraph()
            print('!--- New adjacency found: Updating routing tables ---!')
            self.fullroute = self.fullDijkstra()
            for v in self.g.keys(): #send the vertex routes to each
                self.g[v].updaterouting(self.fullroute[v])

    def printgraph(self):
        res = {}
        for it in self.g:
            print('Node {0} with neighbors: '.format(it))
            print(self.g[it].neighbors)
            print('and priority {0}'.format(self.g[it].priority))
            res.update({it : ({'priority': self.g[it].priority, 'neighbors' : self.g[it].neighbors})})
        return json.dumps(res, indent=4)

    # p: current vertex ng loops and split horizon)
    # b: destination
    # currentcost: sum of the costs until this point
    def __partialDijkstra(self, p, path, b, currentcost):
        if p not in path: # avoid loops and split horizon
            if p in self.g.keys():
                edges = self.g[p].neighbors
                pathcost = -1
                nexthop = None
                p2 = list(path)
                p2.append(p)
                for edge in edges:
                    if b == edge: #direct path
                        if pathcost == -1 or (pathcost > edges[b]["cost"] + currentcost and edges[b]["cost"] !=-1):
                            pathcost = edges[b]["cost"] + currentcost
                            nexthop = b
                    else: #no direct path: we need to jump to the next
                        cost, nh = self.__partialDijkstra(edge, p2, b, currentcost+edges[edge]["cost"])
                        if (pathcost == -1 and cost != -1) or (pathcost > cost and cost !=-1):
                            pathcost = cost
                            nexthop = edge
                return pathcost, nexthop
            else:
                return -1, None
        else:
            return -1, None

    def dijkstraAB(self, a, b):
        if a not in self.g.keys() or b not in self.g.keys():
            return -1, None
        else:
            if len(self.g[b].neighbors) > 0: # only if there is at least a path to the destination
                pathcost = -1
                edges = self.g[a].neighbors
                nexthop = None
                for edge in edges:
                    if b == edge: #direct path
                        if pathcost == -1 or (pathcost > edges[b]["cost"] and edges[b]["cost"] !=-1):
                            pathcost = edges[b]["cost"]
                            nexthop = b
                    else: #no direct path: we need to jump to the next neighbor
                        path = [a]
                        cost, nh = self.__partialDijkstra(edge, path, b, edges[edge]["cost"])
                        if pathcost == -1 or (pathcost > cost and cost !=-1):
                            pathcost = cost
                            nexthop = edge
                return pathcost, nexthop
            else:
                return -1, None

    # there is room for improvement. Once we get the best path from A to B, we can ensure
    # that path is the best from any vertex in within A and B
    def fullDijkstra(self):
        tpath = {}
        for vxs in self.g.keys():
            ppath = {vxs:{}}
            for vxd in self.g.keys():
                lpath = {}
                if vxs != vxd:
                    c, nh = self.dijkstraAB(vxs, vxd)
                    lpath.update({vxd:(c, nh)})
                else:
                    lpath.update({vxd:(0, None)})
                ppath[vxs].update(lpath)
            tpath.update(ppath)
        return tpath

    class vertex:

        def __init__(self, n, p=255):
            self.neighbors = {}
            self.name = n
            self.priority = p
            self.rtable = None

        def addneighbor(self, n, cost, via):
            self.neighbors.update({n.name:{"cost": cost, "via": via}})

        def delneighbor(self, n):
            if n.name in self.neighbors.keys():
                del self.neighbors[n.name]
                return True
            else:
                print('{0} is not connected to {1}'.format(self.name, n.name))
                return False

        def updaterouting(self, routes):
            self.rtable = routes

        def printroutes(self):
            return self.rtable

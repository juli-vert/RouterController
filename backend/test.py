from graph import graph
from tests.tests import Test3

if __name__ == '__main__':
    g1 = Test3()
    opt = input('Pick an option:\n -(list) to check the list of vertex\n \
-(route+vertex_name) to check routing table of vertex_number\n \
-(add+vertex_name+priority) to add a new vertex to the network\n \
-(edge+vertex_source+vertex_dest+cost) to add a new edge\n \
-(remove+vertex_name) to delete the vertex from the network\n \
-(del+vertex_source+vertex_dest) to delete an edge\n \
-(check+vertex_source+vertex_dest) to check the paths from source to dest\n \
-(exit) to exit\n\
:')
    while 1:
        if opt == 'exit':
            break
        elif 'route' in opt:
            if g1.vertexexists(opt.split('+')[1]):
                print(g1.g[opt.split('+')[1]].printroutes())
        elif opt == 'list':
            print(g1.listofvertex())
        elif 'add' in opt:
            if len(opt.split('+')) < 3:
                print('Wrong parameters\n')
            else:
                o, ver, prio = opt.split('+')
                v = graph.vertex(ver, int(prio))
                g1.addvertex(v)
        elif 'edge' in opt:
            if len(opt.split('+')) < 4:
                print('Wrong parameters\n')
            else:
                o, sv, dv, cost = opt.split('+')
                if g1.vertexexists(sv) and g1.vertexexists(dv):
                    g1.addedge(sv, dv, int(cost))
        elif 'remove' in opt:
            if len(opt.split('+')) < 2:
                print('Wrong parameters\n')
            else:
                o, ver = opt.split('+')
                if g1.vertexexists(ver):
                    g1.delvertex(ver)
        elif 'check' in opt:
            if len(opt.split('+')) < 3:
                print('Wrong parameters\n')
            else:
                o, s, d = opt.split('+')
                print(g1.dijkstraAB(s,d))
        elif 'del' in opt:
            if len(opt.split('+')) < 3:
                print('Wrong parameters\n')
            else:
                o, sv, dv = opt.split('+')
                v = g1.deledge(sv,dv)
        else:
            print('Wrong option\n')
        opt = input(':')
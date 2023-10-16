# An SDN controller for Routers

🚧 Work in progress

Routing using the MySPF protocol. A Python Shortest Path First implementation based in a full graph walk-through 

This overlay implements an IP routing protocol over the abstraction layer of MySPF.

Based on a central controller which retrieves/maintains information about the whole network. 
The Controller calculates, using MySPF, the shortest path within all the nodes forming the mesh,  
then the best routes to each connected IP network and push the subset of routes to each router.

New Routers are announced themselves. It means that with a simple configuration, each router is able to register  
itself to the controller.

All the network changes are pushed from the controller, even new interfaces on the routers in the mess are  
are pushed from the controller. The controller is able to find new adjacencies between 2 routers when new  
interfaces are created in the same subnet.


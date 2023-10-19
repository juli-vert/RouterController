# An SDN controller for Routers

🚧 Work in progress:
- A deep refactor is needed  
- Watcher. Add healtcheck endpoints to routers and run a job healtchecking all the endpoints to disable and recalculate the routing when an  
unexpected network topology change is detected.  

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

## Demo

You can run a 6 routers demo using docker using [this docker-compose](demo/docker-compose.yaml)  
Once all the containers are up and running you can access the main GUI by running the [controller](http://localhost:8089/controller)  
The main interface will show up containing 6 routers randomly placed on the main section as shown below  
![Main Window](https://github.com/juli-vert/RouterController/blob/[branch]/main.png?raw=true)

### Actions
#### Move the routers
You can place the routers alongside the main section as your preference
![Action Move](https://github.com/juli-vert/RouterController/blob/[branch]/move.png?raw=true)

#### Context Menu
With the **select** action activated and clicking on each router the **context menu** will be displayed. There are several options:
- add interface
- show routing table
- enter maintenance mode
- open console
- close the menu
![Context menu](https://github.com/juli-vert/RouterController/blob/[branch]/context.png?raw=true)

#### Add interfaces and get links
When adding a new interface in a router the controller will check whether that new interface creates a new link with the existing router's interfaces.  
![Create an Interface](https://github.com/juli-vert/RouterController/blob/[branch]/interface.png?raw=true)
![Link created](https://github.com/juli-vert/RouterController/blob/[branch]/link.png?raw=true)

#### Opening an interactive console
You can manage the routers remotely and try to ping other routers with the console
![Console](https://github.com/juli-vert/RouterController/blob/[branch]/console.png?raw=true)

Each new router can be created afterwards running:
```
docker run --network=mgmt-network --cap-add=NET_ADMIN -p $PORT:$PORT --ip $MANAGEMENT_IP --name $ROUTER_NAME --env-file ./docker/$ROUTER_NAME.env -v //var/run/docker.sock:/var/run/docker.sock sdnrouter
```


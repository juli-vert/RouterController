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
![Main Window](https://github.com/juli-vert/RouterController/blob/main/img/main.png?raw=true)

### Actions
#### Move the routers
You can place the routers alongside the main section as your preference
![Action Move](https://github.com/juli-vert/RouterController/blob/main/img/move.png?raw=true)

#### Context Menu
With the **select** action activated and clicking on each router the **context menu** will be displayed. There are several options:
- add interface
- show routing table
- enter maintenance mode
- open console
- close the menu
![Context menu](https://github.com/juli-vert/RouterController/blob/main/img/context.png?raw=true)

#### Add interfaces and get links
When adding a new interface in a router the controller will check whether that new interface creates a new link with the existing router's interfaces.  
![Create an Interface](https://github.com/juli-vert/RouterController/blob/main/img/interface.png?raw=true)
![Link created](https://github.com/juli-vert/RouterController/blob/main/img/link.png?raw=true)

#### Opening an interactive console
You can manage the routers remotely and try to ping other routers with the console
![Console](https://github.com/juli-vert/RouterController/blob/main/img/console.png?raw=true)

#### Manage networks
You can easily add new networks and check the existing one. You can change the cable color as well
![Network](https://github.com/juli-vert/RouterController/blob/main/img/networks.png?raw=true)

#### Maitenance mode
You can run the topology of this example by executing [those commands](https://github.com/juli-vert/RouterController/blob/main/scripts/steps_notes.sh#L27-L40)

We can run the console to check the interfaces on **R1**
![R1 Interfaces](https://github.com/juli-vert/RouterController/blob/main/img/demo-r1-interfaces.png?raw=true)

with the GUI we can check the running forwarding table:
![R1 Routing Table](https://github.com/juli-vert/RouterController/blob/main/img/demo-r1-routing.png?raw=true)

We can see how it automatically changes when R2 is called to maintenance:
![R1 Routing changes](https://github.com/juli-vert/RouterController/blob/main/img/demo-r1-with-r2-maintenance.png?raw=true)

#### Adding new routers
If we want to simulate that a new router has been connected to the network we can create it afterwards running:
```
docker run --network=mgmt-network --cap-add=NET_ADMIN -p $PORT:$PORT --ip $MANAGEMENT_IP --name $ROUTER_NAME --env-file ./docker/$ROUTER_NAME.env -v //var/run/docker.sock:/var/run/docker.sock sdnrouter
```
This requires to use the **REFRESH** button on the top-left menu.


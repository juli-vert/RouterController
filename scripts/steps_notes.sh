# docker build -t sdnrouter -f ./backend/docker/Dockerfile.router .
# docker build -t sdncontroller -f ./backend/docker/Dockerfile.controller .
# Run the docker-compose in the demo folder to get the environment up & running
## Networks
# docker network create -d bridge --subnet=192.168.255.0/24 --gateway=192.168.255.254 mgmt-network
#   
# docker network create -d bridge --subnet=192.168.102.0/24 --opt icc=true link2
## Containers
# docker run --network=mgmt-network -p 8089:8089 --ip 192.168.255.100 --name controller --env-file ./docker/controller.env sdncontroller
# docker run --network=mgmt-network --cap-add=NET_ADMIN -p 9001:9001 --ip 192.168.255.11 --name r1 --env-file ./docker/R1.env -v //var/run/docker.sock:/var/run/docker.sock sdnrouter
# docker run --network=mgmt-network --cap-add=NET_ADMIN -p 9002:9002 --ip 192.168.255.12 --name r2 --env-file ./docker/R2.env sdnrouter
# docker run --network=mgmt-network --cap-add=NET_ADMIN -p 9003:9003 --ip 192.168.255.13 --name r3 --env-file ./docker/R3.env sdnrouter
## Interfaces
docker network connect demo_link1 demo-r1-1 --ip 192.168.101.11
docker network connect demo_link1 demo-r2-1 --ip 192.168.101.12
docker network connect demo_link2 demo-r2-1 --ip 192.168.102.12
docker network connect demo_link2 demo-r3-1 --ip 192.168.102.13
docker network connect demo_link3 demo-r3-1 --ip 192.168.103.13
docker network connect demo_link3 demo-r4-1 --ip 192.168.103.14
docker network connect demo_link4 demo-r4-1 --ip 192.168.104.14
docker network connect demo_link4 demo-r1-1 --ip 192.168.104.11
docker network connect demo_net1 demo-r1-1 --ip 192.168.201.11
docker network connect demo_net4 demo-r4-1 --ip 192.168.204.14


## Links
curl -X POST "http://127.0.0.1:8089/link?name=demo-r1-1&ip=192.168.101.11&mask=24&cost=10"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r2-1&ip=192.168.101.12&mask=24&cost=10"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r1-1&ip=192.168.102.11&mask=24&cost=80"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r3-1&ip=192.168.102.13&mask=24&cost=80"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r3-1&ip=192.168.103.13&mask=24&cost=140"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r4-1&ip=192.168.103.14&mask=24&cost=140"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r5-1&ip=192.168.103.15&mask=24&cost=140"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r6-1&ip=192.168.103.16&mask=24&cost=140"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r2-1&ip=192.168.104.12&mask=24&cost=50"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r4-1&ip=192.168.104.14&mask=24&cost=50"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r5-1&ip=192.168.104.15&mask=24&cost=50"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r6-1&ip=192.168.104.16&mask=24&cost=50"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r4-1&ip=192.168.204.14&mask=24&cost=60"
curl -X POST "http://127.0.0.1:8089/link?name=demo-r6-1&ip=192.168.201.14&mask=24&cost=60"

curl -X DELETE "http://127.0.0.1:8089/router/demo-r3-1"
curl -X DELETE "http://127.0.0.1:8089/router/demo-r2-1"
curl -X UPDATE "http://127.0.0.1:8089/router/demo-r3-1"
curl -X UPDATE "http://127.0.0.1:8089/router/demo-r2-1"

# docker run -it --rm --privileged --name dockerindocker -v //var/run/docker.sock:/var/run/docker.sock docker

#
#    A ----10----- B
#    |             |
#    50           80
#    |             |
#    C ----140---- D

docker network create -d bridge --subnet=192.168.255.0/24 --gateway=192.168.255.254 mgmt-network
docker network create -d bridge --subnet=192.168.101.0/24 --opt icc=true demo_link1
docker run --network=mgmt-network -p 8089:8089 --ip 192.168.255.100 --name controller --env-file ./docker/controller.env -v //var/run/docker.sock:/var/run/docker.sock sdncontroller
docker run --network=mgmt-network --cap-add=NET_ADMIN -p 9001:9001 --ip 192.168.255.11 --name demo-r1-1 --env-file ./docker/R1.env -v //var/run/docker.sock:/var/run/docker.sock sdnrouter
docker rm -f controller demo-r1-1
docker network rm mgmt-network demo_link1


docker run --network=demo_mgmt-network --cap-add=NET_ADMIN -p 9007:9007 --ip 192.168.255.27 --name demo-r7-1 --env-file ./R7.env -v //var/run/docker.sock:/var/run/docker.sock sdnrouter

docker build -t sdncontroller -f Dockerfile.controller .
docker tag sdncontroller julivert82/routercontroller:sdncontroller
docker push julivert82/routercontroller:sdncontroller

docker tag sdnrouter julivert82/routercontroller:sdnrouter
docker push julivert82/routercontroller:sdnrouter
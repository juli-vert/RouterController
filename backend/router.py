from graph import graph
from flask import json, Flask, make_response, Response, request, jsonify
from ipaddress import ip_address, ip_network, ip_interface
import requests as rq
import subprocess
import logging
import docker as dk
from os import path, getcwd, getenv
import sys
import re

logging.getLogger("werkzeug").setLevel(logging.DEBUG)
rlog = logging.getLogger("werkzeug")

__basefolder = getcwd()
__docker_client = dk.from_env()

app = Flask(__name__)

class router():

    def __init__(self, name, mgmtIP, port, controllerIP, prio=255):
        if ip_address(controllerIP) not in ip_interface(mgmtIP).network.hosts():
            print('Controller IP {0} not in range {1}'.format(str(ip_address(controllerIP)), str(ip_interface(mgmtIP).network)))
        else:
            self.vertex = graph.vertex(name, prio)
            self.ip = ip_interface(mgmtIP)
            self.port = port
            self.controller = ip_address(controllerIP)
            self.interfaces = {}
            self.routes = {}
            params = {'name':name, 'ip': mgmtIP, 'port': port, 'priority': prio}
            r = rq.post('http://{0}:8089/router'.format(controllerIP), params=params)
            print(r)

    def runningRouteTable(self):
        cmd = ["route"]
        rtable = []
        with subprocess.Popen(cmd, stdout=subprocess.Pipe) as sp:
            for line in sp.stdout.readlines():
                if re.match('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}.*', line.decode()):
                    route = list(dict.fromkeys(line.decode().rstrip().split(' '))) # this cleans up the line
                    route.remove('')
                    if route[1] != '0.0.0.0': # exclude directly connected
                        rtable.append(route)
        return rtable

@app.route('/', methods=['GET'])
def routerInfo():
    global __r
    data = {
        "Name": __r.vertex.name,
        "Management IP": str(__r.ip.ip),
        "Management Port": __r.port,
        "Controlled by": str(__r.controller)
    }
    return jsonify(data)

@app.route('/createIface', methods=['POST'])
def createIface():
    global  __r
    global __basefolder
    data = request.json
    __r.interfaces.update(data)
    with open(path.join(__basefolder, f'{__r.vertex.name}_interfaces'), 'w+') as f:
        f.write(json.dumps(__r.interfaces, indent=4))
    for iface in data.keys():
        rlog.info(f"Checking {iface} with {data[iface]}")
        # check whether there is an existing route to the network due discovery which prevents creating the interface
        try:
            routes = None
            with open(path.join(__basefolder, f'{__r.vertex.name}_routes'), 'r') as f:
                fcontent = f.read()
                routes = json.loads(fcontent)
                rlog.info(f"Checking whether {data[iface]['network']['cidr']} is already in route table {routes.keys()}")
                if data[iface]['network']['cidr'] in routes.keys():
                    # remove the route from the local config file
                    del routes[data[iface]['network']['cidr']]
                    cmd = ["route", "del", "-net", data[iface]['network']['cidr']]
                    sp = subprocess.run(cmd, stderr=subprocess.PIPE)
                    if sp.stderr:
                        rlog.info(f"Unable to remove existing routes to {data[iface]['network']['cidr']}")
                    # remove the route from the object
                    del __r.routes[data[iface]['network']['cidr']]
            if routes:
                with open(path.join(__basefolder, f'{__r.vertex.name}_routes'), 'w') as f:
                    f.write(json.dumps(routes, indent=4))
        except FileNotFoundError:
            rlog.info("No existing routes yet")
        finally:
            base_cmd = ["docker", "network", "connect", data[iface]['network']['name'], __r.vertex.name, "--ip", iface]
            rlog.info(f"Applying command: `{' '.join(cmd for cmd in base_cmd)}`")
            sp = subprocess.run(base_cmd, stderr=subprocess.PIPE)
            if sp.stderr:
                rlog.info(f"Unable to add the interface {iface} due {sp.stderr.decode()}")
                return Response(f'Unable to add the interface {iface}', status=400, mimetype='text/plain')
            return Response('Interface saved in running config', status=200, mimetype='text/plain')

@app.route('/routes', methods=['POST'])
def addRouting():
    global __r
    global __basefolder
    global __docker_client
    base_cmd_add = ["route", "add", "-net"]
    base_cmd_del = ["route", "del", "-net"]
    data = json.loads(request.data)
    old_routes = __r.routes
    __r.routes = data
    with open(path.join(__basefolder, f'{__r.vertex.name}_routes'), 'w') as f:
        f.write(json.dumps(__r.routes, indent=4))
    routes_to_remove = list(old_routes.keys())
    for route in data.keys():
        if route in old_routes.keys():
            routes_to_remove.remove(route)
            if old_routes[route] != data[route]:
                # route to be updated
                cmd = base_cmd_del + [route]
                rlog.info(f"Applying command: {cmd} to remove {route}")
                sp = subprocess.run(cmd, stderr=subprocess.PIPE)
                if sp.stderr:
                    rlog.error(f'Unable to delete exiting route to {route} due {sp.stderr.decode()}')
                    return Response({'out': f'Unable to renew route to {route}'}, status=400, mimetype='application/json')
                cmd = base_cmd_add + [route, "gw", data[route]["gateway"].split("/")[0]]
                rlog.info(f"Applying command: {cmd} to readd {route}")
                sp = subprocess.run(cmd, stderr=subprocess.PIPE)
                if sp.stderr:
                    rlog.error(f'Unable to delete exiting route to {route} due {sp.stderr.decode()}')
                    return Response({'out': f'Unable to renew route to {route}'}, status=400, mimetype='application/json')
        else:
            cmd = base_cmd_add + [route, "gw", data[route]["gateway"].split("/")[0]]
            rlog.info(f'Adding to {__r.vertex.name} routing table {route} with gw {data[route]["gateway"].split("/")[0]}')
            sp = subprocess.run(cmd, stderr=subprocess.PIPE)
            if sp.stderr:
                rlog.error(f'Unable to add route to {route} due {sp.stderr.decode()}') #demo-r1-1          | Unable to add route to 192.168.204.0/24 due SIOCADDRT: Network is unreachable
                return Response({'out': f'Unable to add route to {route}'}, status=400, mimetype='application/json')
    for route in routes_to_remove:
        rlog.info(f"Route to be removed: {route}")
        cmd = base_cmd_del + [route]
        subprocess.run(cmd)
    return Response({'out': 'Routes saved in running config'}, status=200, mimetype='application/json')

if __name__ == '__main__':
    try:
        if len(sys.argv) == 6:
            for arg in sys.argv:
                if arg.startswith('name'):
                    name = arg.split("=")[1]
                elif arg.startswith('mgmtip'):
                    mgmtip = arg.split("=")[1]
                    if "/" not in mgmtip:
                        print("wrong management ip format")
                        raise Exception("wrong management ip format")
                elif arg.startswith('port'):
                    port = int(arg.split("=")[1])
                elif arg.startswith('controller'):
                    conip = arg.split("=")[1]
                elif arg.startswith('prio'):
                    prio = arg.split("=")[1]
                elif arg.startswith('router.py'):
                    pass
                else:
                    print('Unknow parameter')
                    raise Exception('unknow parameter')
            __r = router(name, mgmtip, port, conip, prio)
            app.run(host=str(ip_interface(mgmtip).ip), port=port, debug=False)
        elif getenv("ROUTER_NAME", default=None) != None:
            name = getenv("ROUTER_NAME")
            mgmtip = getenv("ROUTER_MGMT_IP")
            port = getenv("ROUTER_PORT")
            conip = getenv("ROUTER_CONTROLLER")
            prio = getenv("ROUTER_PRIORITY")
            __r = router(name, mgmtip, port, conip, prio)
            app.run(host=str(ip_interface(mgmtip).ip), port=port, debug=False)
        else:
            raise Exception('wrong parameters')
    except Exception as e:
        print(e)


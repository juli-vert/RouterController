from graph import graph
from ipaddress import ip_interface, ip_network
from flask import json, Flask, Response, request, render_template, redirect, url_for
from flask_socketio import SocketIO
from flask_cors import CORS, cross_origin
import json
import sys
import os
import pty
import subprocess
import select
import termios
import struct
import fcntl
import shlex
import logging
import requests as rq

__g = None

logging.getLogger("werkzeug").setLevel(logging.INFO)
app = Flask(__name__)

app.config['sessions'] = {}
app.config["cmd"] = ["docker", "exec", "-it"]
app.config["prompt"] = "bash"
CORS(app, supports_credentials=True, resources={r'/*': {'origins': '*'}})
socketio = SocketIO(app, manage_session=False)

class controller(graph):

    def __init__(self, ip='127.0.0.1', p=8088):
        print('Setting up the controller')
        self.ipmgmt = ip_interface(ip)
        self.port = p
        self.managed_networks = {}
        self.loadNetworks()
        self.managed_routers = {}
        self.route_table = {}
        graph.__init__(self)

    def loadNetworks(self):
        nets = os.getenv("NETWORKS")
        for net in nets.split(";"):
            name, ip_range = net.split(":")
            self.managed_networks[name] = ip_range

    def findNetwork(self, ip_ad):
        for net in self.managed_networks.keys():
            if ip_interface(ip_ad).network == ip_network(self.managed_networks[net]):
                return net
        return ""
    
    def addNetwork(self, name, cidr):
        self.managed_networks[name] = cidr

    def getIP(self):
        print(str(self.ipmgmt.ip))
        return str(self.ipmgmt.ip)

    def _findInterface(self, r, n):
        int_r = self.managed_routers[r]["interfaces"]
        int_n = self.managed_routers[n]["interfaces"]
        for intr in int_r:
            for intn in int_n:
                if ip_interface(intr[0]).network == ip_interface(intn[0]).network:
                    return intr[0], intn[0]
        return None, None
    
    def updateIpRouting(self):
        base_routing = self.fullroute
        for router in base_routing.keys():
            routes = {}
            for neig in base_routing[router].keys():
                if neig != router and base_routing[router][neig][1] != None:
                    iface, gw = self._findInterface(router, base_routing[router][neig][1]) # base_routing[router][neig][1] -> next hop to reach neig
                    for route in self.managed_routers[neig]["direct_routes"]:
                        if route not in self.managed_routers[router]["direct_routes"]:
                            if routes.get(route):
                                if routes[route]["cost"] < base_routing[router][neig][0]:
                                    continue
                            routes[route] = ({"gateway": gw, "via": iface, "cost": base_routing[router][neig][0]})
            self.route_table[router] = routes
            r = rq.post('http://{0}:{1}/routes'.format(router, self.managed_routers[router]["port"]), json=routes)
            err = []
            if r.status_code != 200:
                err.append(router)
        return err
    
    def getNetwork(self):
        return self.printgraph()

    def registerRouter(self, name, ip, port, prior):
        v = graph.vertex(name, prior)
        self.managed_routers[name] = {"ip": ip, "port": port, "interfaces": [], "direct_routes": [], "connected": True, "priority": prior}
        out = self.addvertex(v)
        return out
    
    def disableRouter(self, name):
        self.managed_routers[name]["connected"] = False
        self.delvertex(graph.vertex(name))
        self.updateIpRouting()
    
    def enableRouter(self, name):
        if name in self.managed_routers.keys():
            self.managed_routers[name]["connected"] = True
            self.addvertex(graph.vertex(name, self.managed_routers[name]["priority"]))
            reenabled = True
            for iface in self.managed_routers[name]["interfaces"]:
                ok, aux = self.registerIface(name, iface[0], iface[1], reenable=True)
                if not ok:
                    reenabled = False
                    break
            if reenabled:
                self.updateIpRouting()
                return True
            return False
        
    def registerIface(self, name, ip, cost, reenable=False):
        res = []
        exists = False
        if name in self.managed_routers.keys():
            exists = True
        if not exists:
            return 0, res
        else:
            iface = ip_interface(ip)
            if not reenable:
                # First we register the new interface into the managed_routers dictionary
                self.managed_routers[name]['interfaces'].append((str(iface), cost))
                # Second we add the direct route to the list
                self.managed_routers[name]['direct_routes'].append(str(iface.network))
            # Third we check if this new interface generates any new adjacency
            neighbors = []
            out = []
            for node in self.managed_routers.keys():
                if node != name and self.managed_routers[node]['connected']:
                    for mriface in self.managed_routers[node]['interfaces']:
                        if ip_interface(mriface[0]).network == iface.network:
                            neighbors.append(node)
                            cost2 = int(mriface[1])
                            out.append(self.addedge(graph.vertex(name), graph.vertex(node), cost2, cost))
            for a, b in zip(neighbors, out):
                if b == 1:
                    res.append(a)
            return 1, res

@app.route("/")
def main():
    return redirect(url_for('index'))

@app.route("/console")
def console():
    return render_template("console.html")

@app.route("/controller")
def index():
    return render_template("main.html")

@app.route('/network', methods=['GET'])
def getNetwork():
    global __g
    out = __g.getNetwork()
    resp = Response(out, status=200, mimetype='application/json')
    return resp

@app.route('/adjacencies', methods=['GET'])
def getAdjacencies():
    global __g
    out = __g.fullroute
    resp = Response(json.dumps(out, indent=4), status=200, mimetype='application/json')
    return resp

@app.route('/routetable', methods=['GET'])
def getRouting():
    global __g
    out = __g.route_table
    resp = Response(json.dumps(out, indent=4), status=200, mimetype='application/json')
    return resp

@app.route('/routetable/<router>', methods=['GET'])
@cross_origin()
def getRouterRouting(router):
    global __g
    out = __g.route_table[router]
    resp = Response(json.dumps(out, indent=4), status=200, mimetype='application/json')
    return resp

@app.route('/manageddevices', methods=['GET'])
def getDevices():
    global __g
    out = json.dumps(__g.managed_routers, indent=4)
    resp = Response(out, status=200, mimetype='application/json')
    return resp

@app.route('/managednetworks', methods=['GET', 'POST'])
@cross_origin()
def getNetworks():
    global __g
    if request.method == 'GET':
        out = json.dumps(__g.managed_networks, indent=4)
        resp = Response(out, status=200, mimetype='application/json')
        return resp
    elif request.method == 'POST':
        data = request.get_json()
        status = 200
        cmd = ["docker", "network", "create", "-d", "bridge", f"--subnet={data['cidr']}", "--opt", "icc=true", data['name']]
        sp = subprocess.run(cmd, stderr=subprocess.PIPE)
        if sp.stderr:
            logging.info(f"Unable to add a new Network: {data['name']}:{data['cidr']}")
            status = 400
        else:
            __g.addNetwork(data['name'], data['cidr'])
        return Response(json.dumps(__g.managed_networks, indent=4), status=status, mimetype='application/json')
    
@app.route('/router', methods=['POST'])
@cross_origin()
def registerRouter():
    global __g
    rname = request.args.get('name')
    rip = request.args.get('ip')
    rport = request.args.get('port')
    rpriority = request.args.get('priority')
    out = __g.registerRouter(rname, rip, rport, rpriority)
    if out:
        resp = Response('New router added', status=200, mimetype='text/plain')
    else:
        resp = Response('Failed to add router', status=400, mimetype='text/plain')
    return resp

@app.route('/router/<name>', methods=['UPDATE', 'DELETE'])
@cross_origin()
def disableRouter(name):
    global __g
    if request.method == 'DELETE':
        __g.disableRouter(name)
        return Response('Router Disabled', status=200, mimetype='text/plain')
    elif request.method == 'UPDATE':
        out = __g.enableRouter(name)
        if out:
            return Response(f'Router {name} Reenabled', status=200, mimetype='text/plain')
        else:
            return Response(f'Unable to reenable {name}', status=200, mimetype='text/plain')
        
@app.route('/link', methods=['POST'])
@cross_origin()
def registerIface():
    global __g
    rname = request.args.get('name')
    ip = request.args.get('ip')
    mask = request.args.get('mask')
    cost = request.args.get('cost')
    out, neighbors = __g.registerIface(rname, '{0}/{1}'.format(ip, mask), int(cost))

    if out:
        out = '{{ "Node" : "{0}", "Interface" : "{1}", "Neighbors" : ["{2}"] }}'.format(rname, '{0}/{1}'.format(ip, mask), '","'.join(neighbors))
        raddr, rport = __g.managed_routers[rname]['ip'].split('/')[0], __g.managed_routers[rname]['port']
        cidr = str(ip_interface(f'{ip}/{mask}').network)
        params = {f'{ip}': {'network': { "name": __g.findNetwork(f'{ip}/{mask}'), "cidr": f'{cidr}'},'cost': cost}}
        r = rq.post('http://{0}:{1}/createIface'.format(raddr, rport), json=params)
        if r.status_code == 200:
            resp = Response(json.dumps(json.loads(out), indent=4), status=200, mimetype='application/json')
            # Update routing 
            err_routers = __g.updateIpRouting()
            if not err_routers:
                resp = Response(json.dumps(json.loads(out), indent=4), status=200, mimetype='application/json')
            else:
                resp = Response({"Error": f'Link added, but some routers {err_routers} were not able to update their routing tables'}, status=400, mimetype='application/json')
        else:
            resp = Response({"Error": 'Failed to apply interface to router'}, status=400, mimetype='application/json')
    else:
        resp = Response({"Error": 'Router does not exist'}, status=404, mimetype='application/json')
    return resp

def set_winsize(fd, row, col, xpix=0, ypix=0):
    logging.debug("setting window size with termios")
    winsize = struct.pack("HHHH", row, col, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


def read_and_forward_pty_output():
    max_read_bytes = 1024 * 20
    while True:
        socketio.sleep(0.01)
        if app.config["sessions"]:
            timeout_sec = 0
            sessions_to_be_cleaned = []
            for session in app.config["sessions"]:
                (data_ready, _, _) = select.select([app.config["sessions"][session]["fd"]], [], [], timeout_sec)
                if data_ready:
                    output = ""
                    try:
                        output = os.read(app.config["sessions"][session]["fd"], max_read_bytes).decode(errors="ignore")
                    except OSError as err:
                        logging.info("Session has been disconnected")
                    finally:
                        if output == "":
                            sessions_to_be_cleaned.append(session)
                            output = "connection closed"
                            socketio.emit("pty-output", {"output": output}, namespace="/pty", to=session)
                        else:
                            socketio.emit("pty-output", {"output": output}, namespace="/pty", to=session)
            for ses in sessions_to_be_cleaned:
                app.config["sessions"].pop(ses)

@socketio.on("pty-input", namespace="/pty")
def pty_input(data):
    """write to the child pty. The pty sees this as if you are typing in a real
    terminal.
    """
    if app.config["sessions"]:
        if request.sid in app.config["sessions"].keys():
            logging.debug("received input from browser: %s" % data["input"])
            os.write(app.config["sessions"][request.sid]["fd"], data["input"].encode())


@socketio.on("resize", namespace="/pty")
def resize(data):
    if app.config["sessions"]:
        logging.debug(f"Resizing window to {data['rows']}x{data['cols']}")
        if request.sid in app.config["sessions"].keys():
            set_winsize(app.config["sessions"][request.sid]["fd"], data["rows"], data["cols"])


@socketio.on("container", namespace="/pty")
def connect(data):
    """new client connected"""
    logging.info(f"new client connected: {json.dumps(data)} with id: {request.sid}")
    if len(app.config["sessions"]) > 6:
        # MAX console number is 6
        return

    # create child process attached to a pty we can read from and write to
    (child_pid, fd) = pty.fork()
    logging.info(f"New child process created: {child_pid}")
    if child_pid == 0:
        # this is the child process fork.
        spcmd = app.config["cmd"]
        spcmd.append(data['container'])
        spcmd.append(app.config['prompt'])
        subprocess.run(spcmd)
    else:
        # this is the parent process fork.
        app.config["sessions"].update({request.sid : {"fd": fd, "chid": child_pid}})
        set_winsize(fd, 50, 50)
        cmd = " ".join(shlex.quote(c) for c in app.config["cmd"])
        cmd = f"{cmd} {data['container']} {app.config['prompt']}"
        socketio.start_background_task(target=read_and_forward_pty_output)

        logging.info("child pid is " + str(child_pid))
        logging.info(
            f"starting background task with command `{cmd}` to continously read "
            "and forward pty output to client"
        )
        logging.info("task started")

def main():
    global __g
    p = h = False
    for arg in sys.argv:
        if arg.startswith('ip='):
            h = arg.split('=')[1]
        elif arg.startswith('port'):
            p = arg.split('=')[1]
    if not h or not p:
        print("Not all parameters have been met, taking them fron environment")
        h = os.getenv("CONTROLLER_MGMT_IP")
        p = os.getenv("CONTROLLER_PORT")
    if h and p:
        __g = controller(ip=h, p=int(p))
    else:
        print("Not all parameters have been met, running with defaults")
        __g = controller()
    
    green = "\033[92m"
    end = "\033[0m"
    log_format = (
        green
        + "pyxtermjs > "
        + end
        + "%(levelname)s (%(funcName)s:%(lineno)s) %(message)s"
    )
    logging.basicConfig(
        format=log_format,
        stream=sys.stdout,
        level=logging.INFO,
    )
    socketio.run(app, debug=False, port=__g.port, host=__g.getIP())

if __name__ == '__main__':
    main()



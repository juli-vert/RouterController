var functions = ( function() {
	const SELECT = 0;
	const MOVE = 1;
	const LINK = 2;
	const side = 40;
	let action = 0;
	let squares = [];
	let managed_routers = {};
	let managed_networks;
	let menuOn = -1;
	let container = document.getElementById('svg1');
	let height_margin = container.getBoundingClientRect().top;
	let width_margin = container.getBoundingClientRect().left;
	let left_scroll = 0;
	let top_scroll = 0;
	let linksource = {x1: -1, x2: -1, y1: -1, y2: -1}
	let links = {}
	var links2move
	var selectedElem;
	const interface_form = document.getElementById('popup');
	let interface_form_data = {
		router_name: "",
		network_name: "",
		ip_address: "",
		network_mask: "",
		iface_cost: ""
	}
	
	interface_form.classList.add('hidden_input')
	interface_form.addEventListener('submit', (event) => {
		event.preventDefault();
		post_new_interface();
	});

	const isWithin = (a, b, c) => (a>=b & a<=c);
	const isOverlap = (point, rectangle) => (isWithin(rectangle.x));
	const isIn = (point, rectangle) => (isWithin(point.x, rectangle.x, rectangle.x+side) && isWithin(point.y, rectangle.y, rectangle.y+side));

	// re-adjust the left margin when the window is resized (the top one is not gonna change)
	window.onresize = () => {
		width_margin = container.getBoundingClientRect().left;
		menuOn = components.delContextMenu(menuOn)
	}
	// re-adjust the margins when the scroll is activated
	window.onscroll = () => {
		console.log("scroll event launched", container.getBoundingClientRect().left, document.body.scrollLeft)
		left_scroll = document.body.scrollLeft;
		top_scroll = document.body.scrollTop;
		menuOn = components.delContextMenu(menuOn)
	}

	container.addEventListener('mouseup', (e) => {
		if (selectedElem != -1)  {
			document.getElementsByTagName('rect')[selectedElem].setAttribute("fill","rgb(0, 0, 0)")
			selectedElem = -1
			links2move = null
		}
	});

	const showTooltip = (square) => {
		let tooltip = document.getElementById("tooltip");
		tooltip.innerHTML = square.name;
		tooltip.style.display = "block";
		tooltip.style.left = square.x + 20 + width_margin + 'px';
		tooltip.style.top = square.y + 20 + height_margin + 'px';
	}

	const hideTooltip = () => {
		var tooltip = document.getElementById("tooltip");
		tooltip.innerHTML = ""
		tooltip.style.display = "none";
	}

	container.addEventListener('mousemove', (e) => {
		if (action === MOVE && selectedElem !== -1) {
			relocateSquare(e)
		} else {
			square_on = squares.findIndex( square => isIn({x: e.clientX-width_margin+left_scroll, y: e.clientY-height_margin+top_scroll}, square));
			square_on !== -1 ? showTooltip(squares[square_on]) : hideTooltip()
		}
	});

	async function rq(rq_method, url, data=null) {
		let params;
		console.log("Starting a request to: "+url)
		console.log(data)
		if (data !== null ) {
			console.log("I don't expect it here")
			params = {
				method: rq_method,
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(data)
			}
		} else {
			params = {
				method: rq_method,
				headers: {
					'Content-Type': 'application/json'
				}
			}
		}
		const response = await fetch(url, params)
		return response.json()
	};

	async function loadEnvironment () {
		var routers;
		await rq("GET", vars.getUrls()["routers"]).then(data => {
			routers = data
		}).catch(function (error) {
			console.log(error.message)
		});
		for (const [key, element] of Object.entries(routers)) {
			if (!(key in managed_routers)) {
				managed_routers[key] = element
				console.log("adding router: "+key +" with state: "+element['connected'])
				var rect = container.getBoundingClientRect()
				posX = Math.floor(Math.random() * (rect.right - rect.left + 1) + rect.left )
				posY = Math.floor(Math.random() * (rect.bottom - rect.top + 1) + rect.top )
				const aux = {x: posX-width_margin+left_scroll, y:posY-height_margin+top_scroll, name: key, state: element['connected']}
				addSquare(container, aux)
			}
		}
		var cables;
		await rq("GET", vars.getUrls()["links"]).then(data => {
			cables = data
		}).catch(function (error) {
			console.log(error.message)
		});
		for (const [source_router, cable_data] of Object.entries(cables)) {
			const rpos = squares.findIndex(square => square.name === source_router)
			for (const [dest_router, cost] of Object.entries(cable_data["neighbors"])) {
				const dpos = squares.findIndex(square => square.name === dest_router)
				linksource.x1 = squares[rpos]["x"]+side/2
				linksource.y1 = squares[rpos]["y"]+side/2
				linksource.x2 = squares[dpos]["x"]+side/2
				linksource.y2 = squares[dpos]["y"]+side/2
				addLink(container, linksource, squares[rpos], squares[dpos])
			}
		}
		await rq("GET", vars.getUrls()["networks"]).then(data => {
			managed_networks = data
		}).catch(function (error) {
			console.log(error.message)
		});
	}

	const addLink = (elem, coord, src, dst) => {
		if (dst.name in links ? src.name in links[dst.name]? true : false : false) {
			console.log("Link already exists", src.name, dst.name)
		} else {
			console.log("The link must be created between", src.name, dst.name)
			let newlink = document.createElementNS("http://www.w3.org/2000/svg", "line");
			newlink.setAttribute("x1", coord.x1)
			newlink.setAttribute("y1", coord.y1)
			newlink.setAttribute("x2", coord.x2)
			newlink.setAttribute("y2", coord.y2)
			newlink.setAttribute("stroke", "red")
			elem.appendChild(newlink)
			let nodes = [src, dst]
			src["links"].push([newlink, 0])
			dst["links"].push([newlink, 1])
			newlink.addNode = (n) => {
				nodes.push(n)
			}
			newlink.getNodes = () => {
				return nodes
			}
			if (src.name in links) {
				links[src.name][dst.name] = true
			} else {
				links[src.name] = {}
				links[src.name][dst.name] = true
			}
			if (dst.name in links) {
				links[dst.name][src.name] = true
			} else {
				links[dst.name] = {}
				links[dst.name][src.name] = true
			}
			console.log(links)
		}
		
	}

	const addSquare = (elem, aux) => {
		aux["links"] = [] // store the links for each square
		let squares_length = squares.push(aux)
		let newSquare = document.createElementNS("http://www.w3.org/2000/svg", "rect");
		newSquare.setAttribute("width", side)
		newSquare.setAttribute("height", side)
		newSquare.setAttribute("x", aux.x)
		newSquare.setAttribute("y", aux.y)
		if (aux.state == true) {
			newSquare.setAttribute("fill","rgb(0, 0, 0)")
		} else {
			newSquare.setAttribute("fill","rgb(240,128,128)")
		}
		newSquare.addEventListener('click', (e) => {
			if (action === SELECT) {
				const auxMenu = {x: aux.x+width_margin+left_scroll+side/2, y: aux.y+height_margin+top_scroll+side}
				const epos = squares.findIndex(square => square === aux)
				hideTooltip()
				if (menuOn === -1) {
					menuOn = epos;
					components.contextMenu(auxMenu, aux.name, aux.state)
				} else if (menuOn === epos) {
					menuOn = components.delContextMenu(menuOn)
				} else {
					components.delContextMenu(menuOn)
					menuOn = epos
					components.contextMenu(auxMenu, aux.name, aux.state)
				}
			}
		})
		newSquare.addEventListener('mousedown', (e) => {
			if (action === MOVE){
				selectedElem = squares.findIndex( square => isIn({x: e.clientX-width_margin+left_scroll, y: e.clientY-height_margin+top_scroll}, square));
				newSquare.removeAttribute('fill')
				newSquare.setAttribute("fill","rgb(200,200,200)");
				links2move = aux["links"]
			}
		})
		newSquare.getLinks = () => {
			return aux["links"]
		}
		newSquare.removeLink = (l) => {
			idx = aux["links"].findIndex( link => link[0] === l)
			aux["links"].splice(idx,1)
		}
		elem.appendChild(newSquare)
	}

	const removeSquare = (elem) => {
		squares.splice(elem,1)
		let auxelem = document.getElementsByTagName('rect')[elem]
		auxelem.getLinks().forEach(link => {
			link[0].getNodes().forEach(nod => {
				if (nod !== auxelem) {
					nod.removeLink(link[0])
				}
			});
			link[0].parentNode.removeChild(link[0])
		});
		auxelem.parentNode.removeChild(auxelem)
		menuOn = components.delContextMenu(menuOn)
	}

	const relocateSquare = (e) => {
			console.log("The position when the click is finished is: ", e.clientX-width_margin, e.clientY-height_margin)
			document.getElementsByTagName('rect')[selectedElem].setAttribute("x", e.clientX-width_margin+left_scroll)
			document.getElementsByTagName('rect')[selectedElem].setAttribute("y", e.clientY-height_margin+top_scroll)
			squares[selectedElem].x = e.clientX-width_margin+left_scroll
			squares[selectedElem].y = e.clientY-height_margin+top_scroll
			const opt1 = (l) => {
				l.setAttribute("x1", e.clientX-width_margin+left_scroll+side/2)
				l.setAttribute("y1", e.clientY-height_margin+top_scroll+side/2)
			}
			const opt2 = (l) => {
				l.setAttribute("x2", e.clientX-width_margin+left_scroll+side/2)
				l.setAttribute("y2", e.clientY-height_margin+top_scroll+side/2)
			}
			links2move.forEach(link => {
				link[1] ? opt2(link[0]) : opt1(link[0])
			});
	}

	const addInterface = (elem) => {
		let network_options;
		for (const [key, element] of Object.entries(managed_networks)) {
			network_options = network_options + `
			<option value="${key}">${key}:${element}</option>`
			
		}
		const content = `
		<div class="interface-form" id="interface-form">
			<form id="infoform" name="infoform" method="POST">
				<label for="form_network">Network Name</label> 
				<select name="network" id="form_network">
				${network_options}
				</select>
				<input type="text" name="ip" id="form_ip" placeholder="IP Address"/>
				<input type="text" name="cost" id="form_cost" placeholder="Link cost"/>
				<input type="submit" name="submit" value="Submit"/>
			</form>
			<button class="mybtn" onclick="functions.cleanForm()">cancel</button>
		</div>
		`
		interface_form.innerHTML = content
		interface_form.classList.remove('hidden_input')
		console.log(squares[elem])
		interface_form_data.router_name = squares[elem].name
		menuOn = components.delContextMenu(menuOn)
	}

	async function showRouting (elem) {
		var routes;
		await rq("GET", vars.getUrls()["routing"].concat("/",squares[elem].name)).then(data => {
			routes = data
		}).catch(function (error) {
			console.log(error.message)
		});
		console.log(routes)
		var table_lines = ""
		for (const [key, element] of Object.entries(routes)) {
				var table_line = `
				<tr>
				<td>${key}</td>
				<td>${element["gateway"]}</td>
				<td>${element["via"]}</td>
				<td>${element["cost"]}</td>
				</tr>
				`
				table_lines = table_lines + table_line
		}
		const content = `
		<table class="tab1" id="tab1">
              <thead>
                  <tr>
                  <th>Network</th>
                  <th>Next Hop</th>
                  <th>Local Interface</th>
                  <th>Cost</th>
                  </tr>
              </thead>
              <tbody>
				${table_lines}
              </tbody>
        </table>
		<button type="button" onclick="functions.closeTable()">Close</button>
		`
		interface_form.innerHTML = content
		interface_form.classList.remove('hidden_input')
		interface_form.classList.add("wide")
		menuOn = components.delContextMenu(menuOn)
	}

	const closeTable = () => {
		interface_form.innerHTML = ""
		interface_form.classList.add('hidden_input')
		interface_form.classList.remove("wide")
	}

	async function addNetwork() {
		net_name = document.getElementById('netname').value
		cidr = document.getElementById('cidr').value
		json = {
			"name": net_name,
			"cidr": cidr
		}
		await rq("POST", vars.getUrls()["networks"], json).then(data => {
			managed_networks = data
			console.log(data)
		}).catch(function (error) {
			console.log(error.message)
		});
	}

	async function post_new_interface () {
		interface_form_data.network_name = document.getElementById('form_network').value
		interface_form_data.ip_address = document.getElementById('form_ip').value
		interface_form_data.network_mask = (managed_networks[document.getElementById('form_network').value]).split("/")[1]
		interface_form_data.iface_cost = document.getElementById('form_cost').value
		await rq("POST", "http://127.0.0.1:8089/link?name="+interface_form_data.router_name+"&ip="+interface_form_data.ip_address+"&mask="+interface_form_data.network_mask+"&cost="+interface_form_data.iface_cost).then(data => {
			console.log(data)
		}).catch(function (error) {
			console.log(error.message)
		});
		interface_form.innerHTML = ''
		interface_form.classList.add('hidden_input')
	}

	const cleanForm = () => {
		interface_form.innerHTML = ''
		interface_form.classList.add('hidden_input')
		menuOn = components.delContextMenu(menuOn)
	}

	const openConsole = (elem) => {
		router_name = squares[elem].name
		const params = "left=-100,top=-100,location=no,menubar=no,toolbar=no,status=no,width=500,height=500"
		window.open('http://localhost:8089/console?cid='+router_name, 'popup', params)
		menuOn = components.delContextMenu(menuOn)
	}

	async function maintenanceMode(elem) {
		await rq("PATCH", vars.getUrls()["maintenance"].concat("/",squares[elem].name)).then(data => {
			console.log(data)
		}).catch(function (error) {
			console.log(error.message)
		});
		squares[elem].state == true ? document.getElementsByTagName('rect')[elem].setAttribute("fill","rgb(240,128,128)") : document.getElementsByTagName('rect')[elem].setAttribute("fill","rgb(0, 0, 0)")
		squares[elem].state == true ? squares[elem].state = false : squares[elem].state = true
		menuOn = components.delContextMenu(menuOn)
	}

	return {
		LoadEnvironment: () => {
			loadEnvironment()
		},

		ActionSelect: () => {
			action = SELECT;
			for (let item of document.getElementsByClassName("mybtnicon")) {
				if (item.id === "b_select") {
					item.classList.add("mybtnselected")
				} else {
					item.classList.remove("mybtnselected")
				}
			}
		},

		ActionMove: () => {
			action = MOVE;
			for (let item of document.getElementsByClassName("mybtnicon")) {
				if (item.id === "b_move") {
					item.classList.add("mybtnselected")
				} else {
					item.classList.remove("mybtnselected")
				}
			}
		},

		ActionLink: () => {
			action = LINK;
			for (let item of document.getElementsByClassName("mybtnicon")) {
				if (item.id === "b_link") {
					item.classList.add("mybtnselected")
				} else {
					item.classList.remove("mybtnselected")
				}
			}
		},

		getSqLinks: () => {
			sq = document.getElementsByTagName('rect')[document.getElementById("form_links").value]
			sq.getLinks()	 	
		},

		removeSquare: () => {
			removeSquare(menuOn)
		},

		openConsole: () => {
			openConsole(menuOn)
		},

		addInterface: () => {
			addInterface(menuOn)
		},

		showRouting: () => {
			showRouting(menuOn)
		},

		maintenanceMode: () => {
			maintenanceMode(menuOn)
		},

		removeMenu: () => {
			menuOn = components.delContextMenu(menuOn)
		},

		closeTable: () => {
			closeTable()
		},

		addNetwork: () => {
			addNetwork()
		},

		cleanForm: () => {
			cleanForm()
		},

		RefreshEnvironment: () => {
			loadEnvironment()
		}

	};

})();

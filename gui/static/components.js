var components = ( function() {

	return {
		toolbox: () => {
			const tools = vars.toollist()
			let box = document.getElementById("toolbox")
			tools.forEach( (t) => {
				let e1 = document.createElement("div")
				e1.setAttribute("class", "icondiv")
				let b1 = document.createElement("button")
				b1.setAttribute("id", t.id)
				b1.setAttribute("class", t.class)
				b1.setAttribute("onclick", t.onclick)
				let ic1 = document.createElement("EMBED")
				ic1.setAttribute("src", t.icon)
				ic1.setAttribute("class", "icon")
				b1.appendChild(ic1)
				b1.insertAdjacentText("beforeend", t.text)
				e1.appendChild(b1)
				box.appendChild(e1)
			})			
		},

		mycanvas: () => {
			const params = vars.canvasParams()
			let arti= document.getElementsByTagName("article")[0];
			let mainboard = document.createElementNS("http://www.w3.org/2000/svg", "svg");
			mainboard.setAttribute("class", params["class"])
			mainboard.setAttribute("id", params["id"])
			mainboard.setAttribute("xmlns", "http://www.w3.org/2000/svg")
			mainboard.setAttribute("preserveAspectRatio", "xMidYMid meet")
			mainboard.setAttribute("version", "1.1")
			console.log("Screen height: "+window.innerHeight+" / Screen width: "+window.innerWidth)
			var wid = window.innerWidth*3/4-50 > params["width"] ? params["width"] : window.innerWidth*3/4-50
			var hei = window.innerHeight-50 > params["height"] ? window.innerHeight-50 : params["height"]
			const viewbox = "0 0"+wid+" "+hei
			mainboard.setAttribute("viewbox", viewbox)
			mainboard.setAttribute("width", wid)
			mainboard.setAttribute("height", hei)
			arti.appendChild(mainboard)
		}, 

		contextMenu: (pos, name, state) => {
			const menuOptions = vars.menuOpts()
			let rootlist = document.createElement("ul");
			rootlist.setAttribute("id", "activemenu")
			let nelem = document.createElement("li");
			let ntext = document.createTextNode(name);
			nelem.appendChild(ntext);
			nelem.classList.add("boldy");
			rootlist.appendChild(nelem)
			menuOptions.forEach( (o) => {
				let elem = document.createElement("li");
				elem.setAttribute("onclick", o.action);
				let text;
				if (o.text.includes("maintenance mode")) {
					text = state == true ? document.createTextNode("enter "+o.text) : document.createTextNode("leave "+o.text);
				} else {
					text = document.createTextNode(o.text);
				}
				elem.appendChild(text);
				rootlist.appendChild(elem)
			})
			rootlist.style.left = pos.x;
			rootlist.style.top = pos.y;
			document.body.appendChild(rootlist)
		},

		delContextMenu: (state) => {
			if (state != -1) {
				document.getElementById("activemenu").outerHTML = ""
			}
			return -1
		}
	};

})();

var vars = ( function() {
    const tools = [
        {id : "b_select", class: "mybtn mybtnicon mybtnselected", onclick: "functions.ActionSelect()", icon: "./static/icons/mouse-pointer-solid.svg", text: "select"},  
        {id : "b_move", class: "mybtn mybtnicon", onclick: "functions.ActionMove()", icon: "./static/icons/hand-paper-solid.svg", text: "move"},
        {id : "b_reload", class: "mybtn mybtnicon", onclick: "functions.RefreshEnvironment()", icon: "./static/icons/rotate-solid.svg", text: "refresh"} 
    ]

    const mainCanvas = {"class": "mainsvg", "id": "svg1", "width": "1000", "height": "500"}

    const menuOptions = [
        {text: "add interface", action: "functions.addInterface()"},
        {text: "show routing table", action: "functions.showRouting()"},
        {text: "maintenance mode", action: "functions.maintenanceMode()"},
        {text: "open console", action: "functions.openConsole()"},
        {text: "close", action: "functions.removeMenu()"}
    ]

    const urls = {
        "addRouter": "http://127.0.0.1:8080/api/v1/routers",
        "addInterface": "http://127.0.0.1:8089/link",
        "routers": "http://localhost:8089/manageddevices",
        "networks": "http://localhost:8089/managednetworks",
        "links": "http://localhost:8089/network",
        "routing": "http://127.0.0.1:8089/routetable",
        "maintenance":"http://127.0.0.1:8089/router",
    }
    
    return {
        toollist: () => {
            return tools
        }, 
        
        canvasParams: () => {
            return mainCanvas
        },

        menuOpts: () => {
            return menuOptions
        },
        
        getUrls: () => {
            return urls
        }
    };
})();
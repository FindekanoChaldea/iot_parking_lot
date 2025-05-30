import cherrypy
import json
import os
import sys

sys.path.append(os.path.dirname(__file__))

from service_manager import ParkingManager


class ParkingAPI:
    exposed = True

    def __init__(self):
        self.manager = ParkingManager()

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if not uri:
            return {"message": "Available endpoints: /devices, /config"}
        
        if uri[0] == "devices":
            return self.manager.get_device_status()
        
        elif uri[0] == "config":
            return self.manager.get_config()
        
        else:
            cherrypy.response.status = 404
            return {"error": f"Unknown endpoint: /{'/'.join(uri)}"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        if uri and uri[0] == "config":
            data = cherrypy.request.json
            if "total_slots" not in data:
                cherrypy.response.status = 400
                return {"error": "Missing 'total_slots' in request body"}
            
            return self.manager.update_parking_capacity(data["total_slots"])
        
        else:
            cherrypy.response.status = 404
            return {"error": f"Unknown endpoint: /{'/'.join(uri)}"}


if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 9090,  # 与 app.py 使用的端口不同，避免冲突
        'log.screen': True
    })

    config = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')]
        }
    }

    cherrypy.tree.mount(ParkingAPI(), '/', config)
    cherrypy.engine.start()
    cherrypy.engine.block()

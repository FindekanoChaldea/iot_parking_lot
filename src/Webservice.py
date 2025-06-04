import cherrypy
import json
from config_loader import ConfigLoader
config_loader = ConfigLoader()


class Webservice:
    
    exposed = True  
    def __init__(self):
        self.last_post = {}

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        try:
            return self.last_post.pop(uri)
        except KeyError:
            cherrypy.response.status = 404
            return

    @cherrypy.tools.json_in()
    def POST(self, *uri, **params):
        data = cherrypy.request.json
        if not uri:
            if data.lower() == 'newscanner':
                self.last_post[uri] = data
                return "A new scanner is waiting to be initialized"
            if data.lower() == 'newgate':
                self.last_post[uri] = data
                return "A new gate is waiting to be initialized"
            if data.lower() == 'newbot':
                self.last_post[uri] = data
                return "A new bot is waiting to be initialized"
            else:
                self.last_post[uri] = data
        elif uri[0] == 'catalog':
            self.last_post[uri] = data
            return "Data send to Catalog successfully"
        elif uri[0] == 'Interface':
            self.last_post[uri] = data
            return "Data send to Interface successfully"
        elif uri[0] == 'Bot':
            self.last_post[uri] = data
            return "Data send to Bot successfully"
        elif uri[0] == 'devices':
            self.last_post[uri] = data
            return "Data send to Device successfully"
        else:
            self.last_post[uri] = data
            return "Data send successfully"
        
        
if __name__ == '__main__':
    def handle_error(status, message, traceback, version):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps({'message':message})
    cherrypy.config.update({
        'error_page.default': handle_error
    })
    config = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.sessions.on': True
		}
	}

    # Mount the PaymentService class and start the server
    cherrypy.server.socket_host = config_loader.RESTFUL.host
    cherrypy.server.socket_port = config_loader.RESTFUL.port
    cherrypy.tree.mount(Webservice(), '/', config)
    cherrypy.engine.start()
    cherrypy.engine.block()
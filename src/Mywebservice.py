import cherrypy
import os

class Plugin():
	exposed = True
	def __init__(self):
		self.id=1
	def GET(self):
		dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		file_path = os.path.join(dir_path, 'frontend/payment_interface.html')
		return open(file_path).read()



if __name__ == '__main__':



	config = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.staticdir.root': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
		},
		 '/css':{
		 'tools.staticdir.on': True,
		 'tools.staticdir.dir':'./css'
		 },
		 '/js':{
		 'tools.staticdir.on': True,
		 'tools.staticdir.dir':'./js'
		 },
	}


	cherrypy.tree.mount(Plugin(),'/',config)
	cherrypy.engine.start()
	cherrypy.engine.block()
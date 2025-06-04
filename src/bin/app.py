# Here is a basic file of app.py, which is about main logic and API routes.

# Your code here.
import cherrypy
import os
import json
from Parking import Parking
from config_loader import ConfigLoader
import requests
import re
import json
from Catalog import Catalog

config_loader = ConfigLoader()

client_id = 'ParkingSystem'
broker = config_loader.mqtt.broker
port = config_loader.mqtt.port
URL = f"http://{broker}:{port}"
parking = Parking(client_id, broker, port)
parking.run()   



def handle_error(status, message, traceback, version):
    cherrypy.response.headers['Content-Type'] = 'application/json'
    return json.dumps({'message':message})
cherrypy.config.update({
    'error_page.default': handle_error
})
config = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.staticdir.root': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'tools.sessions.on': True,  # Enable sessions
            'tools.sessions.timeout': 1,  # Session timeout in minutes
        },
        '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'frontend/styles.css'
        },
        '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'frontend/script.js'
        },
    }

# Mount the PaymentService class and start the server
cherrypy.server.socket_host = config_loader.payment_api.host
cherrypy.server.socket_port = config_loader.payment_api.port
cherrypy.tree.mount(parking, config_loader.payment_api.uri, config)
cherrypy.engine.start()
cherrypy.engine.block()

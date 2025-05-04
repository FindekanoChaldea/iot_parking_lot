# Here is a basic file of app.py, which is about main logic and API routes.

# Your code here.
import cherrypy
import os
import Parking
import config_loader
import Device

config_loader = config_loader.ConfigLoader()
devices = Device.DeviceManager()

client_id = 'ParkingSystem'
broker = config_loader.mqtt.broker
port = config_loader.mqtt.port
parking = Parking(client_id, broker, port)
parking.connect(devices.entrance1)
parking.connect(devices.entrance2)
parking.connect(devices.exit1)
parking.connect(devices.exit2)
parking.run()
    
    
config = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.staticdir.root': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'tools.sessions.on': True,  # Enable sessions
            'tools.sessions.timeout': 1,  # Session timeout in minutes
        },
        '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './css'
        },
        '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './js'
        },
    }

# Mount the PaymentService class and start the server
cherrypy.server.socket_host = config_loader.payment_api.host
cherrypy.tree.mount(parking, config_loader.payment_api.uri, config)
cherrypy.engine.start()
cherrypy.engine.block()
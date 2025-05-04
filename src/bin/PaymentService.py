import cherrypy
import os

class PaymentService:
    exposed = True
    
    def GET(self):
        """
        Serve the payment_interface.html file.
        """
        dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(dir_path, 'frontend', 'payment_interface.html')
        if not os.path.exists(file_path):
            raise cherrypy.HTTPError(404, "File not found")
        cherrypy.response.headers['Content-Type'] = 'text/html'
        return open(file_path, encoding='utf-8').read()

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        """
        Handle the payment processing logic.
        """
        try:
            # Parse the JSON input
            data = cherrypy.request.json
            plate_license = data.get("plate_license")
            payment_method = data.get("payment_method")
            # Validate input
            if not plate_license or not payment_method:
                raise cherrypy.HTTPError(400, "Missing required fields: plate_license or payment_method")
            
            # Simulate payment processing
            if payment_method == "card":
                status = "COMPLETED"
                message = f"Card payment for plate {plate_license} was successful."
            elif payment_method == "cash":
                status = "COMPLETED"
                message = f"Cash payment for plate {plate_license} was successful."
            else:
                raise cherrypy.HTTPError(400, "Invalid payment method")

            # Return success response
            return {"status": status, "message": message}

        except Exception as e:
            cherrypy.log(f"Error processing payment: {str(e)}")
            raise cherrypy.HTTPError(500, "An error occurred while processing the payment.")

if __name__ == '__main__':
    # Define the configuration for the CherryPy server
    config = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.staticdir.root': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'tools.sessions.on': True,  # Enable sessions
            'tools.sessions.timeout': 120,  # Session timeout in minutes
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
    cherrypy.tree.mount(PaymentService(), '/', config)
    cherrypy.engine.start()
    cherrypy.engine.block()
import paho.mqtt.client as PahoMQTT
import json

class ParkingMQTT:
    def __init__(self, clientID, broker, port, notifier=None):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self.clientID = clientID
        self._topic = ""
        self._isSubscriber = False
        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(client_id =clientID,clean_session = True)
        # register the callback
        self._paho_mqtt.on_connect = self.OnConnect
        self._paho_mqtt.on_message = self.OnMessageReceived
        self._paho_mqtt.on_subscribe = self.OnSubscribe
 
    def OnSubscribe(self, paho_mqtt, userdata, mid, granted_qos):
        print('subscribed to %s'%mid)
        print ("subscribed!" )
        
    def OnConnect (self, paho_mqtt, userdata, flags, rc):
        print ("Connected to %s with result code: %d" % (self.broker, rc))

    def OnMessageReceived (self, paho_mqtt , userdata, msg):
        # A new message is received
        payload = msg.payload.decode('utf-8')
        self.notifier.notify(msg.topic, msg.payload)
 
    def publish (self, topic, msg):
        # publish a message with a certain topic
        self._paho_mqtt.publish(topic, json.dumps(msg), 0)

 
    def subscribe (self, topic):
        
        # subscribe for a topic
        res, mid = self._paho_mqtt.subscribe(topic,0)
        # just to remember that it works also as a subscriber
        self._isSubscriber = True
        self._topic = topic
        print('subscribed to %s'%mid)
 
    def start(self):
        #manage connection to broker
        self._paho_mqtt.connect(self.broker , self.port)
        self._paho_mqtt.loop_start()
    def unsubscribe(self):
        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber 
            self._paho_mqtt.unsubscribe(self._topic)
            
    def stop (self):
        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber 
            self._paho_mqtt.unsubscribe(self._topic)
 
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
        


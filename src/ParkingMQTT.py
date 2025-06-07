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
        self._paho_mqtt.on_unsubscribe = self.OnUnsubscribe
        self._paho_mqtt.on_publish = self.OnPublish
 
    def OnSubscribe(self, paho_mqtt, userdata, mid, granted_qos):
        # print('subscribed to %s'%mid)
        print ("subscribed!" )
        
    def OnUnsubscribe(self, paho_mqtt, userdata, mid):
        # print('unsubscribed from %s'%mid)
        print ("unsubscribed!" )
        
    def OnPublish(self, paho_mqtt, userdata, mid):
        # print('published %s'%mid)
        print ("published!" )
        
    def OnConnect (self, paho_mqtt, userdata, flags, rc):
        print ("Connected to %s with result code: %d" % (self.broker, rc))

    def OnMessageReceived (self, paho_mqtt , userdata, msg):
        # A new message is received
        payload = msg.payload.decode('utf-8')
        self.notifier.notify(msg.topic, msg.payload)
 
    def publish (self, topic, msg):
        # publish a message with a certain topictry:
        try:
            payload = json.dumps(msg)
            self._paho_mqtt.publish(topic, payload, 2)
            print(f"Publishing message: {msg} to topic: {topic}", flush=True)
        except Exception as e:
            print(f"Error in publish: {e}", flush=True)

 
    def subscribe (self, topic):
        
        # subscribe for a topic
        res, mid = self._paho_mqtt.subscribe(topic,2)
        # just to remember that it works also as a subscriber
        self._isSubscriber = True
        self._topic = topic
        print ("subscribing to %s" % (topic))
 
    def start(self):
        #manage connection to broker
        self._paho_mqtt.connect(self.broker , self.port)
        self._paho_mqtt.loop_start()
    def unsubscribe(self, topic):
        # unsubscribe from a topic
        res, mid = self._paho_mqtt.unsubscribe(topic)
        if res == 0:
            print(f"Unsubscribed from topic: {topic}")
        # if (self._isSubscriber):
        #     # remember to unsuscribe if it is working also as subscriber 
        #     self._paho_mqtt.unsubscribe(self._topic)
            
    def stop (self):
        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber 
            self._paho_mqtt.unsubscribe(self._topic)
 
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
        


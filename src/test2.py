from ParkingMQTT import ParkingMQTT as client
import time
import json
import threading

class TestClient:
    def __init__(self, client_id, broker, port):
        self.client = client(client_id, broker, port)
        self.client.start()
        self.topic = "parking/lot1/entrance/entrance_scanner1/info"
        self.client.subscribe(self.topic)
            
    def susbscribe(self, topic):
        self.client.subscribe(topic)
        print(f"Subscribed to topic: {topic}\n")
    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Published message: {message} to topic: {self.topic}\n")
        
if __name__ == "__main__":
    test_client = TestClient("test_client2", "mqtt.eclipseprojects.io", 1883)
    
    # Publish a test message
    test_client.publish("Hello, MQTT!")
    # Keep the script running to listen for messages
    while True:
        time.sleep(1)  # Keep the script alive
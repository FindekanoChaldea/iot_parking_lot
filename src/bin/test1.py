from ParkingMQTT import ParkingMQTT as client
import time
import json
import threading

class TestClient:
    def __init__(self, client_id, broker, port):
        self.client = client(client_id, broker, port, self)
        self.client.start()

    def notify(self, topic, payload): 
        payload = json.loads(payload)
        print(f"[Gate] Received command on topic: {topic} with payload: {payload}")
            
    def susbscribe(self, topic):
        self.client.subscribe(topic)
        
    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Published message: {message} to topic: {self.topic}\n")
    
    def run(self):
        while True:
            time.sleep(2)
if __name__ == "__main__":
    test_client = TestClient("test_client1", "mqtt.eclipseprojects.io", 1883)
    
    # Publish a test message
    test_client.susbscribe("parking/lot_1/entrance/lot_1_entrance_gate_1/command")
    # Keep the script running to listen for messages
    test_client.run()
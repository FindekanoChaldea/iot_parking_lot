from ParkingMQTT import ParkingMQTT as client
import time

class TestClient:
    def __init__(self, client_id, broker, port):
        self.client = client(client_id, broker, port, self)
        self.client.start()
        self.topic = "test/topic"
        self.client.subscribe(self.topic)

    def notify(self, topic, payload):
        print(f"Received message on topic {topic}: {payload.decode('utf-8')}")
    def susbscribe(self, topic):
        self.client.subscribe(topic)
        print(f"Subscribed to topic: {topic}\n")
    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Published message: {message} to topic: {self.topic}\n")
        
if __name__ == "__main__":
    test_client = TestClient("test_client", "mqtt.eclipseprojects.io", 1883)
    
    # Publish a test message
    test_client.susbscribe("parking/lot1/entrance/entrance_scanner1/info")
    
    # Keep the script running to listen for messages
    try:
        while True:
            time.sleep(1)  # Keep the script alive
            pass
    except KeyboardInterrupt:
        print("Exiting...")
        test_client.client.stop()
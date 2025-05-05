from Gate import Gate
import time
       
client_id = 'EntranceGate1'
broker = "mqtt.eclipseprojects.io"
port = 1883
pub_topic = 'polito_parking/entrance/gate1/info'
sub_topic = 'polito_parking/entrance/gate1/command'
entranceGate1 = Gate(client_id, broker, port, pub_topic, sub_topic)
while True:
    time.sleep(1)  # Keep the script running to listen for messages
from Gate import Gate
import time 

client_id = 'ExitGate2'
broker = "mqtt.eclipseprojects.io"
port = 1883
pub_topic = 'polito_parking/exit/gate2/info'
sub_topic = 'polito_parking/exit/gate2/command'
exitGate2 = Gate(client_id, broker, port, pub_topic, sub_topic)
while True: 
    time.sleep(1)
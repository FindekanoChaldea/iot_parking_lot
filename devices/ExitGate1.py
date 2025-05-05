from Gate import Gate
import time

client_id = 'EntranceGate1'
broker = "mqtt.eclipseprojects.io"
port = 1883
pub_topic = 'polito_parking/entrance/gate1/info'
sub_topic = 'polito_parking/entrance/gate1/command'
exitGate1 = Gate(client_id, broker, port, pub_topic, sub_topic)
exitGate1.run()
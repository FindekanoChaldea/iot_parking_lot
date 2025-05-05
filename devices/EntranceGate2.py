from Gate import Gate
       
client_id = 'EntranceGate2'
broker = "mqtt.eclipseprojects.io"
port = 1883
pub_topic = 'polito_parking/entrance/gate2/info'
sub_topic = 'polito_parking/entrance/gate2/command'
entranceGate2 = Gate(client_id, broker, port, pub_topic, sub_topic)
entranceGate2.run()
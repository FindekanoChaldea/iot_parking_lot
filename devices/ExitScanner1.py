
from Scanner import Scanner

client_id = 'EntranceScanner1'
broker = "mqtt.eclipseprojects.io"
port = 1883
pub_topic = 'polito_parking/entrance/scanner1/info'
sub_topic = 'polito_parking/entrance/scanner1/command'
exitScanner1 = Scanner(client_id, broker, port, pub_topic, sub_topic)
exitScanner1.run()     
                
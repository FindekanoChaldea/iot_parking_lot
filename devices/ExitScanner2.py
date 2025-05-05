from Scanner import Scanner
import time

client_id = 'EntranceScanner2'
broker = "mqtt.eclipseprojects.io"
port = 1883
pub_topic = 'polito_parking/entrance/scanner2/info'
sub_topic = 'polito_parking/entrance/scanner2/command'
exitScanner2 = Scanner(client_id, broker, port, pub_topic, sub_topic)   
exitScanner2.run()
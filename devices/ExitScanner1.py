import Scanner

if __name__ == "__main__":
    client_id = 'EntranceScanner1'
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    pub_topic = 'polito_parking/entrance/scanner1/info'
    sub_topic = 'polito_parking/entrance/scanner1/command'
    entranceScanner = Scanner(client_id, broker, port, pub_topic, sub_topic)
    entranceScanner.run()
                
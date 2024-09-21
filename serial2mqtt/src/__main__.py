import os
import time
import json
import logging
import paho.mqtt.client as mqtt
from datetime import datetime
from serial import Serial, SerialException

SERIAL_DEVICE = os.environ['SERIAL_DEVICE']
BAUDRATE = int(os.environ['BAUDRATE'])
MQTT_TOPIC = os.environ['MQTT_TOPIC']
MQTT_RETAIN = os.environ['MQTT_RETAIN'] == "true"
MQTT_HOST = os.environ['MQTT_HOST']
MQTT_PORT = int(os.environ['MQTT_PORT'])
MQTT_USERNAME = os.environ['MQTT_USERNAME']
MQTT_PASSWORD = os.environ['MQTT_PASSWORD']
SEND_ACK = os.environ['SEND_ACK'] == "true"
DEBUG = os.environ['DEBUG'] == "true"

if DEBUG:
    LOGLEVEL = os.environ.get('LOGLEVEL', 'DEBUG').upper()
else:
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()


def wait_for_serial_device() -> Serial:
    while True:
        try:
            serial = Serial(SERIAL_DEVICE, BAUDRATE, timeout=1)
            logging.info(f"Connected to {SERIAL_DEVICE} at {BAUDRATE} baud")
            return serial
        except SerialException:
            pass
        time.sleep(1)

def listen_to_serial(serial: Serial, mqtt_client: mqtt.Client):
    while True:
        line: str = serial.readline().decode('utf-8').strip()
        timestamp = datetime.now().isoformat()
        if line.startswith("ERROR:"):
            logging.error(f"{timestamp} - {line}")
        elif line != "":
            try:
                data = json.loads(line)
                if SEND_ACK:
                    serial.write(1) # send ack
                if "id" in data:
                    topic = f'{MQTT_TOPIC}/{data["id"]}'
                else:
                    topic = MQTT_TOPIC
                if "timestamp" not in data:
                    data["timestamp"] = timestamp
                logging.debug(f"Publishing '{data}' to {topic}")
                mqtt_client.publish(topic, payload=json.dumps(data), qos=0, retain=MQTT_RETAIN)
            except ValueError as e:
                logging.debug(f"{timestamp} - Ignoring non JSON message: {line}")

def mqtt_connect(client, userdata, flags, rc):
    if rc != 0:
        logging.critical("Could not connect. Error: " + str(rc))
    else:
        logging.info("Connected to MQTT server")
        client.publish(f'{MQTT_TOPIC}/status', payload="online", qos=0, retain=True)

def mqtt_disconnect(client, userdata, rc):
    logging.critical("Lost connection to MQTT server : " + mqtt.connack_string(rc))

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=LOGLEVEL, datefmt='[%H:%M:%S]')

    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.on_connect = mqtt_connect
    mqtt_client.on_disconnect = mqtt_disconnect
            
    logging.info('Serial to MQTT started')
    while True:
        logging.info('Waiting for serial connection..')
        try:
            serial = wait_for_serial_device()
            mqtt_client.will_set(f'{MQTT_TOPIC}/status', payload="offline", qos=0, retain=True)
            mqtt_client.connect_async(MQTT_HOST, port=MQTT_PORT, keepalive=60)
            mqtt_client.loop_start() # i think this is needed to stop incoming messages from blocking us from publishing
            listen_to_serial(serial, mqtt_client)
        except Exception as e:
            logging.error(e)
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
import os
import sys
import time
import json
import logging
import paho.mqtt.client as mqtt
from datetime import datetime
from serial import Serial, SerialException

SERIAL_DEVICE = os.environ['SERIAL_DEVICE']
BAUDRATE = int(os.environ['BAUDRATE'])
MQTT_TOPIC = os.environ['MQTT_TOPIC']
MQTT_SUB_TOPIC_FIELD = os.environ['MQTT_SUB_TOPIC_FIELD']
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

mqtt_connected = False

def listen_to_serial(serial: Serial, mqtt_client: mqtt.Client):
    global mqtt_connected
    while True:
        line: str = serial.readline().decode('utf-8').strip()
        if line == "":
            continue
        if line.startswith("ERROR:"):
            logging.error(line[6:])
            continue
        if mqtt_connected == False:
            logging.warning(f"Message '{line}' lost due to missing MQTT connection.")
            if SEND_ACK:
                logging.debug("Sending negative ack to serial device")
                serial.write(b'-') # send negative ack
            continue
        try:
            timestamp = datetime.now().isoformat()
            data = json.loads(line)
            if SEND_ACK:
                logging.debug("Sending ack to serial device")
                serial.write(b'+') # send ack
            if MQTT_SUB_TOPIC_FIELD in data:
                topic = f'{MQTT_TOPIC}/{data[MQTT_SUB_TOPIC_FIELD]}'
            else:
                topic = MQTT_TOPIC
            if "timestamp" not in data:
                data["timestamp"] = timestamp
            logging.debug(f"Publishing '{data}' to {topic}")
            mqtt_client.publish(topic, payload=json.dumps(data), qos=0, retain=MQTT_RETAIN)
        except ValueError:
            logging.warning(line)

def mqtt_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc != 0:
        logging.critical("Could not connect to MQTT broker:" + mqtt.connack_string(rc))
    else:
        logging.info(f"Connected to local MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        mqtt_connected = True
        client.publish(f'{MQTT_TOPIC}/status', payload="online", qos=0, retain=True)

def mqtt_disconnect(client, userdata, rc):
    global mqtt_connected
    logging.warning("Lost connection to MQTT broker: " + mqtt.connack_string(rc))
    mqtt_connected = False

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=LOGLEVEL, datefmt='[%H:%M:%S]')

    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.on_connect = mqtt_connect
    mqtt_client.on_disconnect = mqtt_disconnect
            
    logging.info('Serial to MQTT started')

    try:
        logging.debug(f"Trying to connect to local MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        mqtt_client.will_set(f'{MQTT_TOPIC}/status', payload="offline", qos=0, retain=True)
        mqtt_client.connect_async(MQTT_HOST, port=MQTT_PORT, keepalive=60)
        mqtt_client.loop_start() # i think this is needed to stop incoming messages from blocking us from publishing
        while True:
            try:
                logging.debug(f"Trying to connect to {SERIAL_DEVICE} at {BAUDRATE} baud")
                serial = Serial(SERIAL_DEVICE, BAUDRATE, timeout=1)
                logging.info(f"Connected to {SERIAL_DEVICE} at {BAUDRATE} baud")
                listen_to_serial(serial, mqtt_client)
            except SerialException as e:
                if 'could not open port' in str(e):
                    logging.debug(e)
                else:
                    logging.warning(e)
                time.sleep(1)
            finally:
                if serial.isOpen():
                    logging.info("Closing serial connection")
                    serial.close()
    except Exception as e:
        logging.critical(e)
        sys.exit(1)
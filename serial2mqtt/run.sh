#!/usr/bin/with-contenv bashio

CONFIG_PATH=/data/options.json

export SERIAL_DEVICE=$(bashio::config "serial_device")
export BAUDRATE=$(bashio::config "baudrate")
export DEBUG=$(bashio::config "debug")
export MQTT_TOPIC=$(bashio::config 'mqtt_base_topic')
export MQTT_SUB_TOPIC_FIELD=$(bashio::config 'mqtt_sub_topic_field')
export MQTT_RETAIN=$(bashio::config 'mqtt_retain')
export SEND_ACK=$(bashio::config 'send_ack')

export MQTT_USERNAME=$(bashio::services "mqtt" "username")
export MQTT_PASSWORD=$(bashio::services "mqtt" "password")
export MQTT_HOST=$(bashio::services "mqtt" "host")
export MQTT_PORT=$(bashio::services "mqtt" "port")

set -e

bashio::log.blue "Running Serial to MQTT.."

bashio::log.info "Serial Device =" $SERIAL_DEVICE
bashio::log.info "Baudrate =" $BAUDRATE
bashio::log.info "Sending Acks =" $SEND_ACK
bashio::log.info "MQTT Topic =" $MQTT_TOPIC
bashio::log.info "MQTT Sub Topic Field =" $MQTT_SUB_TOPIC_FIELD
bashio::log.info "MQTT Retain =" $MQTT_RETAIN
bashio::log.info "MQTT Host =" $MQTT_HOST
bashio::log.info "MQTT Port =" $MQTT_PORT
bashio::log.info "MQTT User =" $MQTT_USERNAME
bashio::log.info "MQTT Password =" $(echo $MQTT_PASSWORD | sha256sum | cut -f1 -d' ')
bashio::log.info "DEBUG =" $DEBUG

python serial2mqtt
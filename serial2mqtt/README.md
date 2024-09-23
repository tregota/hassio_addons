# Serial to MQTT Bridge Addon

**This addon listens for JSON data on a given serial device and passes it to the installed MQTT broker.**  
If the JSON data has the given sub topic field (default: id) then that value is added to the topic path e.g: "serial/{id}".  
A timestamp is added if missing from the JSON data.  
If configured to send ack, will write '+' back to the serial interface for every recieved valid JSON and is mostly for my [ESP-NOW Receiver project](https://github.com/tregota/esp-now-receiver) which receives ESP-NOW messages and passes it to serial via USB or UART

**In configuration.yaml, you can manually add entities like this for the metrics you want to keep track of**  
```
mqtt:
  sensor:
    - name: "Doorbell Battery"
      unique_id: "doorbell.battery"
      state_topic: "serial/doorbell"
      unit_of_measurement: "%"
      value_template: "{{ value_json.batterylevel }}"
      device_class: "battery"
```

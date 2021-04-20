# MQTT-Simulator **WORK IN PROGRESS**
MQTT simulator for some basic elements like thermometers, cameras or some actuators.

You can configure your simulation with config.json file or in the actual program in the table.
There is a possibility to change the broker IP address and port, add new devices and change them at runtime.

You will need to install PyQT.

---------------------

# MQTT Camera Simulator
Script to simulate a security camera with a default system camera.

This script will work with Raspberry Pi with CSI or USB camera or with an ordinary laptop with webcam.

**Arguments:**
- -a --address - MQTT broker IP address. The camera image will be send to this broker. Default: 127.0.0.1
- -p --port - MQTT broker port. Default: 1883
- -u --update - Camera image update time in seconds. Default: 1 second
- -t --topic - Topic that will define the camera image on broker. Default: home/living-room/camera

**Example:** ``python cameraToMQTT.py --address 192.168.1.150 --port 1990 --update 10 --topic "home/bedroom/camera"``
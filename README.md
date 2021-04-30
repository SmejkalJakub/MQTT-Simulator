# MQTT-Simulator **WORK IN PROGRESS**
MQTT simulator for some basic elements like thermometers, cameras or some actuators.

You can configure your simulation with config.json file or in the actual program in the table.
There is a possibility to change the broker IP address and port, add/remove devices and change them at runtime.

You will need to install PyQT5 with ``sudo apt-get install python3-pyqt5`` or with ``pip install PyQt5``
Or you can run ``pip install -r requirements.txt`` to install all the required packages for both simulators

**Arguments:**
- -n --no-ui - will run this script without showing the UI (for terminal usage)
- -h --help - shows the help message and ends the script with code 1
- -c --config - sets the configuration file(json format) that should be used for the app. Default "config.json".


**Configuration file example (JSON format)**
```json
{
    "broker": "192.168.1.100",
    "broker-port": 1883,
    "mqtt_devices": [
        {
            "device_type": "thermometer",
            "images_dir": "None",
            "json_dir": "None",
            "name": "Teplomer pokoj",
            "publish_time": 1000,
            "subscribe": 0,
            "topic": "home/living-room/temperature",
            "type": "value",
            "value": "20",
            "value_low": "15",
            "value_top": "25"
        },
        {
            "device_type": "camera",
            "images_dir": "images",
            "json_dir": "None",
            "name": "Kamera vstup",
            "publish_time": 0,
            "subscribe": 0,
            "topic": "home/entry/camera",
            "type": "image",
            "value": "None",
            "value_low": "None",
            "value_top": "None"
        },
        {
            "device_type": "humidity meter",
            "images_dir": "None",
            "json_dir": "None",
            "name": "Vlhkomer lo\u017enice",
            "publish_time": 1000,
            "subscribe": 0,
            "topic": "home/bedroom/humidity",
            "type": "value",
            "value": "30",
            "value_low": "45",
            "value_top": "70"
        }
    ]
}

```

**Device configuration description**

- ``device_type`` - type of device like thermometer or camera. Just for organization.
- ``images_dir`` - path to the directory from where the images should be taken from. Relevant only when the ``type`` is set to "image".
- ``json_dir`` - path to the directory from where the json files should be taken from. Relevant only when the ``type`` is set to "json". 
- ``name`` - name of the device, just for organization.
- ``publish_time`` - time interval that specifies how often the message should be published. Format is in milliseconds.
- ``subscribe`` - if this value is set to the 1 the device will update the ``value`` field if some message is published to the ``topic``. The value 0 is changed to No and 1 is changed to Yes.
- ``topic`` - the topic associated with the device.
- ``type`` - type of message that will be send. Possible types are "value", "image", "json".
- ``value`` - current value presented on the device. This field is used only if the ``type`` is set to "value". After this field is changed in the UI message will be published to the associated ``topic``.
- ``value_low`` - this field is the lowest value that can be published to the ``topic`` associated with the device. Only relevant if the ``type`` is set to "value".
- ``value_top`` -  this field is the highest value that can be published to the ``topic`` associated with the device. Only relevant if the ``type`` is set to "value". ``value_low`` and ``value_top`` sets the borders. Every time the message of the device with ``type`` value should be published, random value between these borders will be published.


**Known bugs**

If you want to remove the device you will need to select cell of the device you want to remove. 

(Bug) - After the device is removed the app will be restarted for simplicity (UI only)

(Bug) - If you start the script with all the ``publish_time`` set to 0 you will need to restart the app after any of the ``publish_time`` is set to non zero value. If there is any device with a non zero ``publish_time`` you don't have to restart after setting the ``publish_time`` on any other device.

---------------------

# MQTT Camera Simulator
Script to simulate a security camera with a default system camera.

This script will work with Raspberry Pi that has CSI or USB camera. 
Also, it can work with an ordinary laptop with a webcam.

**Arguments:**
- -a --address - MQTT broker IP address. The camera image will be send to this broker. Default: 127.0.0.1
- -p --port - MQTT broker port. Default: 1883
- -u --update - Camera image update time in seconds. Default: 1 second
- -t --topic - Topic that will define the camera image on broker. Default: home/living-room/camera

**Example:** ``python cameraToMQTT.py --address 192.168.1.150 --port 1990 --update 10 --topic "home/bedroom/camera"``
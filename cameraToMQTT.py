"""
    Script to simulate security camera with a default system camera.

    This script will work with Raspberry Pi with CSI or USB camera or with an ordinary laptop with webcam.

    You need to install python-opencv

    Author: Jakub Smejkal (xsmejk28)
"""

import cv2
import sys
import time
import getopt
import paho.mqtt.client as mqtt

if __name__ == '__main__':
    
    # Default arguments
    brokerAddress = '127.0.0.1'
    brokerPort = 1883
    updateTime = 1
    topic = 'home/living-room/camera'

    # Handle Arguments
    short_options = "a:p:u:t:"
    long_options = ["address=", "port=", "update=", "topic="]
    
    arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)

    for argument, value in arguments:
        if argument in ("-a", "--address"):
            brokerAddress = value
        elif argument in ("-p", "--port"):
            brokerPort = int(value)
        elif argument in ("-u", "--update"):
            updateTime = float(value)
        elif argument in ("-t", "--topic"):
            topic = value

    # Create MQTT client and try to connect
    client = mqtt.Client()

    try:
        client.connect(brokerAddress, brokerPort, 60)
    except:
        print("Can't connect to MQTT broker")
        exit(-1)

    # Start non blocking client loop
    client.loop_start()

    # Start capturing on default system camera
    cam = cv2.VideoCapture(0)
    print("Starting sending images from camera")

    while True:
        camFounded, frame = cam.read()
        
        if(not camFounded):
            print("Camera not found - Breaking loop")
            break

        # Encode the frame into memory buffer and convert it to bytes
        _, imageBuffer = cv2.imencode(".jpg", frame)
        imageBufferBytes = imageBuffer.tobytes()

        # Send the image bytes over MQTT
        client.publish(topic, imageBufferBytes)

        # Wait before another frame
        time.sleep(updateTime)

    print("Sending stopped")

    # Release camera after we are done
    cam.release()

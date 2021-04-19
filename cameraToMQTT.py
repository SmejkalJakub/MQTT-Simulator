import cv2
import sys
import time
import getopt
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    global connected
    connected = True
    
def on_disconnect(client, userdata, rc):
   global connected
   connected = False

def on_message(client, userdata, msg):
    pass

if __name__ == '__main__':
    brokerAddress = '127.0.0.1'
    brokerPort = 1883
    updateTime = 1
    topic = 'home/living-room/camera'

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

    client = mqtt.Client()

    try:
        client.connect(brokerAddress, brokerPort, 60)
    except:
        print("Can't connect to MQTT broker")
        exit(-1)

    client.loop_start()

    cam = cv2.VideoCapture(0)

    print("Starting sending images from camera")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("camera not found")
            break

        _, im_buf_arr = cv2.imencode(".jpg", frame)
        byte_im = im_buf_arr.tobytes()
        client.publish(topic, byte_im)

        time.sleep(updateTime)

    print("sending stopped")
    cam.release()
    cv2.destroyAllWindows()

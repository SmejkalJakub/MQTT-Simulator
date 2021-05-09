"""
MQTT Simulator for experimenting with MQTT messages

This code was created for school project and bachelor thesis

Authors: Jakub Smejkal (xsmejk28)
         Tomas Stanek (xstane44)
"""

import io
import os
import sys
import json
import time
import sched
import getopt
import string
import random
import threading
import PIL.Image as Image
import paho.mqtt.client as mqtt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDateTime, Qt, QTimer

connected = False
scheduler = sched.scheduler(time.time, time.sleep)

stopFlag = False

schedulerEvents = {}

selectedItem = None

class WidgetGallery(QDialog):
    def __init__(self, client, data, config, brokerAddress="127.0.0.1", parent=None):
        super(WidgetGallery, self).__init__(parent)

        self.setFixedWidth(900)
        self.originalPalette = QApplication.palette()
        self.config = config

        # Some basic QApplication setup
        label = QLabel('Broker')

        if(connected):
            self.connectedLabel = QLabel("Connected")
        else:
            self.connectedLabel = QLabel("Disconnected")

        button = QPushButton('Connect')
        button.clicked.connect(self.on_connect_button_clicked)
        self.lineEdit = QLineEdit(brokerAddress)

        topLayout = QHBoxLayout()
        topLayout.addWidget(label)
        topLayout.addWidget(self.lineEdit)
        topLayout.addWidget(button)
        topLayout.addWidget(self.connectedLabel)
        topLayout.addStretch(1)

        addDevicehbox = QHBoxLayout()
        addDeviceButton = QPushButton('Add Device')
        addDeviceButton.clicked.connect(self.addDeviceButtonClick)
        addDevicehbox.addWidget(addDeviceButton)

        self.removeDeviceButton = QPushButton('Remove Device')
        self.removeDeviceButton.clicked.connect(self.removeDeviceButtonClick)
        self.removeDeviceButton.setEnabled(False)
        addDevicehbox.addWidget(self.removeDeviceButton)
        # End of basic setup

        # Load JSON data and setup the table widget
        self.jsonData = json.loads(data)
        numberOfDevices = len(self.jsonData['mqtt_devices'])


        keys = [
            "device_type",
            "images_dir",
            "json_dir",
            "name",
            "publish_time",
            "subscribe",
            "topic",
            "type",
            "value",
            "value_low",
            "value_top",
        ]
        
        self.tableWidget = QTableWidget(numberOfDevices, len(keys))

        #keys = list(self.jsonData['mqtt_devices'][0].keys())

        self.tableWidget.setHorizontalHeaderLabels(keys)

        for (row, device) in enumerate(self.jsonData['mqtt_devices']):
            for (collumn, value) in enumerate(device.values()):
                self.addItem(self.tableWidget, row, collumn, value)

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()

        self.tableWidget.cellChanged.connect(self.cellChanged)
        self.tableWidget.itemSelectionChanged.connect(self.itemSelected)

        tab1hbox = QHBoxLayout()
        tab1hbox.setContentsMargins(5, 5, 5, 5)
        tab1hbox.addWidget(self.tableWidget)

        mainLayout = QGridLayout()
        mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        mainLayout.addLayout(tab1hbox, 1, 0, 2, 4)
        mainLayout.addLayout(addDevicehbox, 3, 0, 3, 4)

        self.setLayout(mainLayout)
        self.setWindowTitle("MQTT Simulator")

    # Register item selection change
    def itemSelected(self):
        global selectedItem

        selectedItem = self.tableWidget.currentItem().row()
        self.removeDeviceButton.setEnabled(True)

    # Add new item to the device
    def addItem(self, table, row, column, value):
        keys = list(self.jsonData['mqtt_devices'][0].keys())

        if(keys[column] == "subscribe"):
            if(value == 1):
                value = "Yes"
            else:
                value = "No"

        newItem = QTableWidgetItem(str(value))
        table.setItem(row, column, newItem)

    # Remove button click callback(WORK IN PROGRESS)
    def removeDeviceButtonClick(self):
        global selectedItem
        
        del self.jsonData['mqtt_devices'][selectedItem]

        saveJson(json.dumps(self.jsonData), self.config)
        os.execl(sys.executable, sys.executable, *sys.argv)

    # Add new device to the end of list 
    def addDeviceButtonClick(self):

        newItem = { 
                    "device_type": "newItem",
                    "images_dir": "None",
                    "json_dir": "None",
                    "name": "Please Fill",
                    "publish_time": 0,
                    "subscribe": 0,
                    "topic": "Please Fill Topic",
                    "type": "none",
                    "value": "20",
                    "value_low": "0",
                    "value_top": "0"
                  }
                
        self.jsonData['mqtt_devices'].append(newItem)

        self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)

        saveJson(json.dumps(self.jsonData), self.config)

        for (collumn, value) in enumerate(self.jsonData['mqtt_devices'][self.tableWidget.rowCount() - 1].values()):
            self.addItem(self.tableWidget, self.tableWidget.rowCount() - 1, collumn, value)

    # If app is closed all the scheduled functions should be stopped
    def closeEvent(self, test):
        global stopFlag 
        stopFlag = True

    # Callback detecting change of a cell
    def cellChanged(self, row, column):
        keys = list(self.jsonData['mqtt_devices'][row].keys())

        if(keys[column] == "value"):
            client.publish(self.tableWidget.item(row, 6).text(), self.tableWidget.item(row, column).text())

        if(keys[column] == "subscribe"):
            if(self.tableWidget.item(row, column).text() == "Yes"):
                self.jsonData['mqtt_devices'][row][keys[column]] = 1
            else:
                self.jsonData['mqtt_devices'][row][keys[column]] = 0
        elif(keys[column] == "publish_time"):
            self.jsonData['mqtt_devices'][row][keys[column]] = int(self.tableWidget.item(row, column).text())
        else:  
            self.jsonData['mqtt_devices'][row][keys[column]] = self.tableWidget.item(row, column).text()
        
        resetTask(json.dumps(self.jsonData), row, client)

        saveJson(json.dumps(self.jsonData), self.config)

    # Connect button callback that will try to connect to selected MQTT broker
    def on_connect_button_clicked(self):
        client.disconnect()
        client.loop_stop()
        
        self.jsonData["broker"] = self.lineEdit.text()
        saveJson(json.dumps(self.jsonData), self.config)

        os.execl(sys.executable, sys.executable, *sys.argv)

    # This function is called whenever the MQTT message is received and it changes the value of desired cell
    def changeValue(self, topic, message):
        for row in range(0, self.tableWidget.rowCount()):
            if(self.tableWidget.item(row, 6).text() == topic):
                self.tableWidget.item(row, 8).setText(message)
                self.tableWidget.resizeColumnsToContents()
                self.jsonData['mqtt_devices'][row]['value'] = self.tableWidget.item(row, 8).text()
                saveJson(json.dumps(self.jsonData), self.config)

#---------------------------------------------------------------------------------------------------------------------------------------------------------

# Callback when MQTT client is connected
def on_connect(client, userdata, flags, rc):
    global connected
    connected = True
    
# Callback when MQTT client is disconnected
def on_disconnect(client, userdata, rc):
   global connected
   connected = False

# For test purposes if we want to subscribe to all topics
def subscribeToAllTopics(client):
    client.subscribe("#", 1)

# Simple function to subscribe to topic
def subscribeToTopic(client, topic):
    client.subscribe(topic, 1)

# This function will be called periodicaly for each topic that should send messages periodicaly
def publish_message(data, scheduler, client, index):
    jsonData = json.loads(data)

    global stopFlag

    if(connected):
        if(jsonData['type'] == 'value'):
            publishValue(json.dumps(jsonData))
        elif(jsonData['type'] == 'image'):
            publishImage(json.dumps(jsonData))
        elif(jsonData['type'] == 'json'):
            publishJson(json.dumps(jsonData))

    if(not stopFlag):
        schedulerEvents[index] = scheduler.enter(jsonData['publish_time'] / 1000, 2, publish_message, (json.dumps(jsonData), scheduler, client, index,))

# Function to save the configuration if anything changes
def saveJson(data, fileName):
    with open(configFile, 'w') as outFile:
        outFile.write(json.dumps(json.loads(data), indent=4, sort_keys=True))

# This function serves to reset task after the cell change
def resetTask(data, index, client):
    jsonData = json.loads(data)
    rowData = jsonData['mqtt_devices'][index]

    if(index in schedulerEvents.keys()):
        scheduler.cancel(schedulerEvents[index])
        if(rowData['publish_time'] == 0):
            del schedulerEvents[index]

    if(rowData['publish_time'] != 0 and rowData['topic'] != "" and rowData['topic'] != "Please Fill Topic"):
        scheduler.enter(rowData['publish_time'] / 1000, 2, publish_message, (json.dumps(rowData), scheduler, client, index,))

# Simple function to send basic value over MQTT
def publishValue(data):
    jsonData = json.loads(data)
    client.publish(jsonData['topic'], random.randint(int(jsonData['value_low']), int(jsonData['value_top'])))

# Simple function to send random image from folder as byte array over MQTT
def publishImage(data):
    jsonData = json.loads(data)

    pathToFolder = jsonData['images_dir']
    if(not os.path.exists(pathToFolder)):
        print("Images folder path does not exist")
        return
    if(len(os.listdir(pathToFolder)) == 0):
        print("Images folder is empty")
        return

    randomFile = random.choice(os.listdir(pathToFolder))
    with open(pathToFolder + "/" + randomFile, "rb") as image:
        f = image.read()
        byteArray = bytearray(f)

    client.publish(jsonData['topic'], byteArray)

# Simple function to send random json data from folder over MQTT array
def publishJson(data):
    jsonData = json.loads(data)

    pathToFolder = jsonData['json_dir']
    if(not os.path.exists(pathToFolder)):
        print("Json folder path does not exist")
        return
    if(len(os.listdir(pathToFolder)) == 0):
        print("Json folder is empty")
        return

    randomFile = random.choice(os.listdir(pathToFolder))
    with open(pathToFolder + "/" + randomFile, "rb") as jsonFile:
        jsonFromFile = json.load(jsonFile)

    data_out=json.dumps(jsonFromFile)
    client.publish(jsonData['topic'], data_out)

# This function will update all the devices in config.json
def updateDevices(data):
    jsonData = json.loads(data)

    for idx, deviceData in enumerate(jsonData['mqtt_devices']):
        if(deviceData['publish_time'] != 0 and deviceData['topic'] != "" and deviceData['topic'] != "Please Fill Topic"):
            scheduler.enter(deviceData['publish_time'] / 1000, 2, publish_message, (json.dumps(deviceData), scheduler, client, idx,))

        if(deviceData['subscribe']):
            if(deviceData['topic'] != "" and deviceData['topic'] != "Please Fill Topic"):
                subscribeToTopic(client, deviceData['topic'])

# The callback for when a PUBLISH message is received from the mqtt server.
def on_message(client, userdata, msg):
    # Change the value present in table
    gallery.changeValue(msg.topic, (msg.payload).decode('utf-8'))

def showHelp():
    print("\nMQTT simulator that will send MQTT messages based on configuration file\n")
    print("Arguments: ")
    print("\t-n --no-ui: will run this script without showing the UI (for terminal usage)")
    print("\t-h --help: Shows this message and ends the script with code 1")

if __name__ == '__main__':
    
    showUI = True
    configFile = "config.json"

    # Handle Arguments
    short_options = "nhc:"
    long_options = ["no-ui", "help", "config="]
    
    try:
        arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
    except:
        print("\nWrong arguments")
        showHelp()
        exit(-1)

    for argument, value in arguments:
        if argument in ("-n", "--no-ui"):
            showUI = False
        if argument in ("-h", "--help"):
            showHelp()
            exit(1)
        if argument in ("-c", "--config"):
            if(os.path.exists(value) and value.endswith((".json"))):
                configFile = value
            else:
                print("\nChoose existing configuration file")
                showHelp()
                exit(-1)


    # Load the data from config
    with open(configFile) as f:
        data = json.load(f)

    # Start and configure MQTT Client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect(data['broker'], data['broker-port'], 60)
    updateDevices(json.dumps(data))
    
    # Start the scheduler;
    t = threading.Thread(target=scheduler.run)
    t.start()

    # Start listening loop without blocking the whole program
    client.loop_start()

    print("Starting sending messages to the broker: " + str(data['broker']) + " on port: " + str(data['broker-port']))

    # Create the QApplication UI
    if(showUI):
        app = QApplication([])
        gallery = WidgetGallery(brokerAddress=data['broker'], client=client, data=json.dumps(data), config=configFile)
        gallery.show()

        sys.exit(app.exec_())

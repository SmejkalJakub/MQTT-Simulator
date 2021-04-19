import io
import os
import sys
import json
import time
import sched
import string    
import random
import threading
import PIL.Image as Image
from PyQt5.QtWidgets import *
import paho.mqtt.client as mqtt
from PyQt5.QtCore import QDateTime, Qt, QTimer

connected = False
scheduler = sched.scheduler(time.time, time.sleep)

stopFlag = False

schedulerEvents = {}

selectedItem = None

class WidgetGallery(QDialog):
    def __init__(self, client, data, brokerAddress="127.0.0.1", parent=None, ):
        super(WidgetGallery, self).__init__(parent)

        self.setFixedWidth(900)

        self.originalPalette = QApplication.palette()

        #self.createTopLeftGroupBox()
        #self.createTopRightGroupBox()
        #self.createBottomLeftTabWidget()
        #self.createBottomRightGroupBox()
        #self.createProgressBar()

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

        self.jsonData = json.loads(data)

        numberOfDevices = len(self.jsonData['mqtt_devices'])

        self.tableWidget = QTableWidget(numberOfDevices, len(self.jsonData['mqtt_devices'][0].keys()))

        keys = list(self.jsonData['mqtt_devices'][0].keys())

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

    def itemSelected(self):
        global selectedItem

        print(self.tableWidget.currentItem())
        selectedItem = self.tableWidget.currentItem().row()
        self.removeDeviceButton.setEnabled(True)


    def addItem(self, table, row, column, value):
        keys = list(self.jsonData['mqtt_devices'][0].keys())

        if(keys[column] == "subscribe"):
            if(value == 1):
                value = "Yes"
            else:
                value = "No"

        newItem = QTableWidgetItem(str(value))
        table.setItem(row, column, newItem)

    def removeDeviceButtonClick(self):
        global selectedItem
        self.tableWidget.removeRow(selectedItem)

        _selectedItem = selectedItem + 1

        print(self.tableWidget.getItem(selectedItem))

        del self.jsonData['mqtt_devices'][_selectedItem]

        if(_selectedItem in schedulerEvents.keys()):
            scheduler.cancel(schedulerEvents[_selectedItem])

        for i in range(selectedItem, self.tableWidget.rowCount()):
            print(i)

        self.removeDeviceButton.setEnabled(False)

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

        saveJson(json.dumps(self.jsonData))

        for (collumn, value) in enumerate(self.jsonData['mqtt_devices'][self.tableWidget.rowCount() - 1].values()):
            self.addItem(self.tableWidget, self.tableWidget.rowCount() - 1, collumn, value)

    def closeEvent(self, test):
        global stopFlag 
        stopFlag = True

    def cellChanged(self, row, column):
        keys = list(self.jsonData['mqtt_devices'][row].keys())

        print(column)
        print(keys[column])

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

        saveJson(json.dumps(self.jsonData))

    def on_connect_button_clicked(self):
        client.disconnect()
        client.loop_stop()

        try:
            client.connect(self.lineEdit.text(), 1883, 60)

            client.loop_start()
            subscribeToAllTopics(client)

            self.connectedLabel.setText("Connected")
        except:
            self.connectedLabel.setText("Disconnected")

    def changeValue(self, topic, message):

        for row in range(0, self.tableWidget.rowCount()):
            if(self.tableWidget.item(row, 6).text() == topic):
                self.tableWidget.item(row, 8).setText(message)
                self.tableWidget.resizeColumnsToContents()
                self.jsonData['mqtt_devices'][row]['value'] = self.tableWidget.item(row, 8).text()
                saveJson(json.dumps(self.jsonData))

    


def on_connect(client, userdata, flags, rc):
    global connected
    connected = True
    
def on_disconnect(client, userdata, rc):
   global connected
   connected = False

def subscribeToAllTopics(client):
    client.subscribe("#", 1)

def subscribeToTopic(client, topic):
    client.subscribe(topic, 1)

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

#---------------------------------------------------------------------------------------------------------------------------------------------------------

def saveJson(data):
    outFile = open("config.json", "w")
    outFile.write(json.dumps(json.loads(data), indent=4, sort_keys=True))
    outFile.close()

def resetTask(data, index, client):
    if(index in schedulerEvents.keys()):
        scheduler.cancel(schedulerEvents[index])

    jsonData = json.loads(data)
    rowData = jsonData['mqtt_devices'][index]

    if(rowData['publish_time'] != 0 and rowData['topic'] != "" and rowData['topic'] != "Please Fill Topic"):
        scheduler.enter(rowData['publish_time'] / 1000, 2, publish_message, (json.dumps(rowData), scheduler, client, index,))

def publishValue(data):
    jsonData = json.loads(data)

    client.publish(jsonData['topic'], random.randint(int(jsonData['value_low']), int(jsonData['value_top'])))

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

if __name__ == '__main__':
    
    # Load the data from config
    if(os.path.exists('config.json')):
        with open('config.json') as f:
            data = json.load(f)
    else:
        f = open('config.json', 'x')

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

    # Create the QApplication UI
    app = QApplication([])
    gallery = WidgetGallery(brokerAddress=data['broker'], client=client, data=json.dumps(data))
    gallery.show()

    sys.exit(app.exec_()) 
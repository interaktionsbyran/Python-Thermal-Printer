#!/usr/bin/python

# Listens to topic amee/interaktionight/print on mqtt broker at
# m2m.interaktionsbyran.se
#
# Required software includes Adafruit_Thermal, Python Imaging and PySerial
# libraries. Other libraries used are part of stock Python install.

from __future__ import print_function
from PIL import Image
# from io import BytesIO
#import requests
from StringIO import StringIO
import json
import paho.mqtt.client as mqtt
# from Adafruit_Thermal import *

# printer   = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)
host      = 'm2m.interaktionsbyran.se'
topic     = 'amee/interaktionight/print'


# response = requests.get(url)
# img = Image.open(BytesIO(response.content))
# or
# Image.open(StringIO(urlopen(url).read()))


def on_message(mqttc, obj, msg):
  #print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
  payload = json.loads(msg.payload)
  
  # TODO: print divider and NIB logo

  username = payload['username']
  # printer.boldOn()
  # printer.println(username)
  # printer.boldOff()

  if payload.has_key('image') == True:
    url = payload['image']['url']
    width = payload['image']['width']
    height = payload['image']['height']
    img = Image.open(StringIO(urlopen(url).read()))
    img = img.convert('1') # convert to B&W (use 'L' for monochrome)
    # printer.printImage(img, True)

  caption = payload['caption']
  # printer.println(caption)

  # TODO: print divider and feed the printer
  # printer.feed(3)


mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.connect(host, 1883, 60)
mqttc.subscribe(topic, 0)

mqttc.loop_forever()

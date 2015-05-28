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
import urllib2
import json
from StringIO import StringIO
import paho.mqtt.client as mqtt
from Adafruit_Thermal import *
from image_resize import aspect_fit

printer   = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)
host      = 'm2m.interaktionsbyran.se'
topic     = 'amee/interaktionight/print'
logo      = Image.open("gfx/interaktionight.png")

def on_message(mqttc, obj, msg):
  print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
  payload = json.loads(msg.payload)
  
  # TODO: print divider and NIB logo

  username = payload['username']
  printer.printImage(logo)
  printer.feed(2)

  if payload.has_key('image') == True:
    url = payload['image']['url']
    print(url)
    width = payload['image']['width']
    height = payload['image']['height']
    try:
      headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.5.17 (KHTML, like Gecko) Version/8.0.5 Safari/600.5.17'}
      req = urllib2.Request(url, None, headers)
      data = urllib2.urlopen(req).read()
      img = Image.open(StringIO(data))
      img = aspect_fit(img, 384, 384)
      img = img.convert('1') # convert to B&W (use 'L' for monochrome)
      printer.printImage(img, True)
    except Exception, e:
      # The image is not valid
      print(e)

  printer.justify('C')
  printer.boldOn()
  printer.setSize('S')
  printer.println("Greetings from")
  printer.setSize('L')
  printer.println('@' + username)
  printer.setSize('S')
   
  caption = payload['caption']
  printer.feed(1)
  printer.println('"' + caption + '"')
  printer.feed(1)
  printer.setSize('S')
  printer.boldOff()
  printer.underlineOn()
  printer.println('www.interaktionsbyran.se')
  printer.underlineOff()
  printer.feed(2)
  printer.println('_____________________________')
  printer.feed(4)


mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.connect(host, 1883, 60)
mqttc.subscribe(topic, 0)

mqttc.loop_forever()

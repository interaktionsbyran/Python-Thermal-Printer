# -*- coding: utf-8 -*-
#!/usr/bin/python

# Follows the omnibus spec
#
# MUST BE RUN AS ROOT (due to GPIO access)
#
# Required software includes Adafruit_Thermal, Python Imaging and PySerial
# libraries. Other libraries used are part of stock Python install.

from __future__ import print_function
from PIL import Image
import subprocess, time, socket
import urllib2
import json
from StringIO import StringIO
import paho.mqtt.client as mqtt
from Adafruit_Thermal import *
from image_resize import aspect_fit
import RPi.GPIO as GPIO


printer         = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)
ledPin          = 18
buttonPin       = 23
holdTime        = 2     # Duration for button hold (shutdown)
tapTime         = 0.01  # Debounce time for button taps
#host            = 'm2m.interaktionsbyran.se'
host            = 'vegas'
logo            = Image.open("gfx/tc.png")
OUTPUT_NAME     = 'iotp'
OUTPUT_CLASS    = 'selfiePrinter'

# Called when button is held down.  Prints image, invokes shutdown process.
def hold():
	GPIO.output(ledPin, GPIO.HIGH)
	printer.printImage(Image.open('gfx/goodbye.png'), True)
	printer.feed(3)
	subprocess.call("sync")
	subprocess.call(["shutdown", "-h", "now"])
	GPIO.output(ledPin, GPIO.LOW)

def tap():
	# Show IP address (if network is available)
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('8.8.8.8', 0))
		printer.print('My IP address is ' + s.getsockname()[0])
		printer.feed(3)
	except:
		printer.boldOn()
		printer.println('Network is unreachable.')
		printer.boldOff()
		printer.print('Connect display and keyboard\n'
		  'for network troubleshooting.')
		printer.feed(3)
		exit(0)


def on_connect(client, userdata, flags, rc):
	print("Connected with result code "+str(rc))
	# Since we're not streaming we listen to everyone that wants 
	# to send stuff without first subscribing
	mqttc.subscribe('source/+/' + OUTPUT_CLASS)
	report_presence()


def report_presence():
	payload = json.dumps({
		'name': OUTPUT_NAME,
		'description': 'Thermal selfie printer', 
		'descriptionImage': '', 
		'outputClass': OUTPUT_CLASS
		},
		sort_keys=False)

	mqttc.publish('output/presence/' + OUTPUT_NAME, payload=payload, qos=0, retain=True)


def on_message(mqttc, obj, msg):
	GPIO.output(ledPin, GPIO.HIGH)  # LED on while working
	print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
	payload = json.loads(msg.payload)
  
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
	printer.println('@' + str(username))
	printer.setSize('S')
   
	caption = payload['caption']
	printer.feed(1)
	printer.println('"' + caption.encode('cp437', 'ignore') + '"')
	printer.feed(1)
	printer.setSize('S')
	printer.boldOff()
	printer.underlineOn()
	printer.println('www.technocreatives.com')
	printer.underlineOff()
	printer.feed(2)
	printer.println('_____________________________')
	printer.feed(4)
	GPIO.output(ledPin, GPIO.LOW)


# Initialization

# Use Broadcom pin numbers (not Raspberry Pi pin numbers) for GPIO
GPIO.setmode(GPIO.BCM)

# Enable LED and button (w/pull-up on latter)
GPIO.setup(ledPin, GPIO.OUT)
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# LED on while working
GPIO.output(ledPin, GPIO.HIGH)

# Processor load is heavy at startup; wait a moment to avoid
# stalling during greeting.
time.sleep(30)

# print IP if available
tap()

# Print greeting image
printer.printImage(Image.open('gfx/hello.png'), True)
printer.feed(3)
GPIO.output(ledPin, GPIO.LOW)

mqttc = mqtt.Client()
mqttc.will_set('output/presence/' + OUTPUT_NAME, None, 0, True)
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.connect(host, 1883, 60)


#mqttc.loop_forever()
mqttc.loop_start()

# Poll initial button state and time
prevButtonState = GPIO.input(buttonPin)
prevTime        = time.time()
tapEnable       = False
holdEnable      = False

while 1:
	# Poll current button state and time
	buttonState = GPIO.input(buttonPin)
	t           = time.time()

	# Has button state changed?
	if buttonState != prevButtonState:
		prevButtonState = buttonState   # Yes, save new state/time
		prevTime        = t
	else:                             # Button state unchanged
		if (t - prevTime) >= holdTime:  # Button held more than 'holdTime'?
			# Yes it has.  Is the hold action as-yet untriggered?
			if holdEnable == True:        # Yep!
				hold()                      # Perform hold action (usu. shutdown)
				holdEnable = False          # 1 shot...don't repeat hold action
				tapEnable  = False          # Don't do tap action on release
		elif (t - prevTime) >= tapTime: # Not holdTime.  tapTime elapsed?
			# Yes.  Debounced press or release...
			if buttonState == True:       # Button released?
				if tapEnable == True:       # Ignore if prior hold()
					tap()                     # Tap triggered (button released)
					tapEnable  = False        # Disable tap and hold
					holdEnable = False
			else:                         # Button pressed
				tapEnable  = True           # Enable tap and hold actions
				holdEnable = True

	# LED blinks while idle, for a brief interval every 2 seconds.
	# Pin 18 is PWM-capable and a "sleep throb" would be nice, but
	# the PWM-related library is a hassle for average users to install
	# right now.  Might return to this later when it's more accessible.
	if ((int(t) & 1) == 0) and ((t - int(t)) < 0.15):
		GPIO.output(ledPin, GPIO.HIGH)
	else:
		GPIO.output(ledPin, GPIO.LOW)


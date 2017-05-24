import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from sense_hat import SenseHat
import json
import os
import time
import sys
import threading
import netifaces as ni

sense = SenseHat()

red = (255, 0, 0)
green = (0, 255, 0)

print("Waiting for internet access...")
start = time.time()
end = time.time()
while end-start < 30:
    sense.show_message("Connecting...", text_colour=red)
    end = time.time()
sense.show_message(" OK ", text_colour=green)


THINGSBOARD_HOST = '192.168.51.140'
ACCESS_TOKEN = 'jxMm1OoiyxipoVRubFWM'

# Data capture and upload interval in seconds. Less interval will eventually hang the DHT22.
INTERVAL=30

sensor_data = {'temperature': 0, 'humidity': 0}

next_reading = time.time() 

client = mqtt.Client()

# Set access token
client.username_pw_set(ACCESS_TOKEN)

# Connect to Thingsboard using default MQTT port and 60 seconds keepalive interval
client.connect(THINGSBOARD_HOST, 1883, 60)

client.loop_start()

ip_address = {'ip': 0}

def getIp():
	# Try to get wlan0, otherwise eth0
	try:
		ni.ifaddresses('wlan0')
		ip = ni.ifaddresses('wlan0')[2][0]['addr']
	except:
		ni.ifaddresses('eth0')
		ip = ni.ifaddresses('eth0')[2][0]['addr']
	print(ip)
	ip_address['ip'] = ip

	# Sending IP address
	client.publish('v1/devices/me/attributes', json.dumps(ip_address), 1)

try:
    count = 0
    while True:
	
        sense.show_message("Data")

        humidity = round(sense.get_humidity(), 2)
        temperature = round(sense.get_temperature(), 2)
        print(u"Temperature: {:g}\u00b0C, Humidity: {:g}%".format(temperature, humidity))
        sensor_data['temperature'] = temperature
        sensor_data['humidity'] = humidity

        # Sending humidity and temperature data to Thingsboard
        client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)

        next_reading += INTERVAL
        sleep_time = next_reading-time.time()
	
	count += 1
	if count > 10:
		getIp()
		count = 0
	
        if sleep_time > 0:
            time.sleep(sleep_time)
except KeyboardInterrupt:
    pass

client.loop_stop()
client.disconnect()

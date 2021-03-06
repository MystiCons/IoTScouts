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

def printPixels():
  X = [0, 255, 0]  # Green
  O = [0, 0, 0] # White

  pixel_fin = [
  X, O, O, O, O, O, O, X,
  O, O, O, O, O, O, O, O,
  O, O, O, O, O, O, O, O,
  O, O, O, X, X, O, O, O,
  O, O, O, X, X, O, O, O,
  O, O, O, O, O, O, O, O,
  O, O, O, O, O, O, O, O,
  X, O, O, O, O, O, O, X
  ]
  sense.set_pixels(pixel_fin)
  time.sleep(2)
  sense.clear()

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
ACCESS_TOKEN = 'CE6CaB6wLYCVO8b7FwXL' # This must be changed

# Data capture and upload interval in seconds. Less interval will eventually hang the DHT22.
INTERVAL=30

sensor_data = {'temperature': 0, 'humidity': 0, 'air_pressure': 0}

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
  global client
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
    printPixels()
    humidity = round(sense.get_humidity(), 2)
    temperature = round(sense.get_temperature(), 2)
    air_pressure = round(sense.get_pressure(), 2)
    print(u"Temperature: {:g}\u00b0C, Humidity: {:g}%, Pressure: {}hpa".format(temperature, humidity, air_pressure))
    sensor_data['temperature'] = temperature
    sensor_data['humidity'] = humidity
    sensor_data['air_pressure'] = air_pressure

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

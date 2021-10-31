#!/usr/bin/env python3

import ssl
import sys
import re
import json
import os.path
import argparse
from time import time, sleep, localtime, strftime
from collections import OrderedDict
from colorama import init as colorama_init
from colorama import Fore, Back, Style
from configparser import ConfigParser
from unidecode import unidecode
import paho.mqtt.client as mqtt
import serial
import sdnotify
from signal import signal, SIGPIPE, SIG_DFL
from datetime import datetime
signal(SIGPIPE,SIG_DFL)

project_name = 'Schellenberg Stick MQTT Client/Daemon'
project_url = 'https://github.com/moTo31/schellenberg-mqtt'

deviceBaudRate = 9600
deviceEnumeratorKey = 'deviceEnumerator'
deviceCommandKey = 'command'

commandMap = {'stop' : '00',
              'up' : '01',
              'down' : '02',
              'windowHandle0' : '1A',
              'windowHandle90' : '1B',
              'windowHandle180' : '3B'
             }

# parameters = OrderedDict([
#     (MI_LIGHT, dict(name="LightIntensity", name_pretty='Sunlight Intensity', typeformat='%d', unit='lux', device_class="illuminance")),
#     (MI_TEMPERATURE, dict(name="AirTemperature", name_pretty='Air Temperature', typeformat='%.1f', unit='°C', device_class="temperature")),
#     (MI_MOISTURE, dict(name="SoilMoisture", name_pretty='Soil Moisture', typeformat='%d', unit='%', device_class="humidity")),
#     (MI_CONDUCTIVITY, dict(name="SoilConductivity", name_pretty='Soil Conductivity/Fertility', typeformat='%d', unit='µS/cm')),
#     (MI_BATTERY, dict(name="Battery", name_pretty='Sensor Battery Level', typeformat='%d', unit='%', device_class="battery"))
# ])

if False:
    # will be caught by python 2.7 to be illegal syntax
    print('Sorry, this script requires a python3 runtime environment.', file=sys.stderr)

# Argparse
parser = argparse.ArgumentParser(description=project_name, epilog='For further details see: ' + project_url)
parser.add_argument('--config_dir', help='set directory where config.ini is located', default=sys.path[0])
parse_args = parser.parse_args()

# Intro
colorama_init()
print(Fore.GREEN + Style.BRIGHT)
print(project_name)
print('Source:', project_url)
print(Style.RESET_ALL)

# Systemd Service Notifications - https://github.com/bb4242/sdnotify
sd_notifier = sdnotify.SystemdNotifier()

# Logging function
def print_line(text, error = False, warning=False, sd_notify=False, console=True):
    timestamp = strftime('%Y-%m-%d %H:%M:%S', localtime())
    if console:
        if error:
            print(Fore.RED + Style.BRIGHT + '[{}] '.format(timestamp) + Style.RESET_ALL + '{}'.format(text) + Style.RESET_ALL, file=sys.stderr)
        elif warning:
            print(Fore.YELLOW + '[{}] '.format(timestamp) + Style.RESET_ALL + '{}'.format(text) + Style.RESET_ALL)
        else:
            print(Fore.GREEN + '[{}] '.format(timestamp) + Style.RESET_ALL + '{}'.format(text) + Style.RESET_ALL)
    timestamp_sd = strftime('%b %d %H:%M:%S', localtime())
    if sd_notify:
        sd_notifier.notify('STATUS={} - {}.'.format(timestamp_sd, unidecode(text)))


# Eclipse Paho callbacks - http://www.eclipse.org/paho/clients/python/docs/#callbacks
def on_connect(client, userdata, flags, rc):
    global loop_flag
    loop_flag = 0
    if rc == 0:
        print_line('MQTT connection established', console=True, sd_notify=True)
        print()
    else:
        print_line('Connection error with result code {} - {}'.format(str(rc), mqtt.connack_string(rc)), error=True)
        #kill main thread
        os._exit(1)


def on_publish(client, userdata, mid):
    #print_line('Data successfully published.')
    pass

def validateJsonCommand(jsonData):
  bValid = False
  try:
    resultMap = json.loads(jsonData)
    if deviceEnumeratorKey in resultMap and deviceCommandKey in resultMap:
      device = resultMap[deviceEnumeratorKey]
      command = resultMap[deviceCommandKey]
      if command in commandMap.keys():
        bValid = True
      else:
        print_line('Invalid command (not in map) received: ' + command, error=True, sd_notify=True)
  except ValueError as err:
      return False
  return bValid

def buildSchellenbergCommand(device, command):
  fullCommand = 'ss' + \
                device + \
                numOfResends + \
                commandMap[command] + \
                '0000\n' #0000 is the Padding, newline at the end is required because it fails otherwise
  return fullCommand


def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    #print_line('Received new command, checking it..' + payload, console=True, sd_notify=True)
    bValid = validateJsonCommand(payload)
    jsonObj = json.loads(payload)
    if bValid:
        device = jsonObj[deviceEnumeratorKey]
        command = jsonObj[deviceCommandKey]      
        fullCommand = buildSchellenbergCommand(device, command)
        print_line('New command:' + fullCommand, console=False, sd_notify=True)
        #write the command to the port
        try:
            #set up serial connection to usb stick
            ser = serial.Serial('/dev/' + usb_adapter, deviceBaudRate)
            numBytes = ser.write(str.encode(fullCommand))
            ser.close() # do not keep the connection open if others want to use it as well
            sleep(1.0) # wait some time for the next command to be executed
        except serial.SerialException as e:
            print_line('Error setting command to serial port ' + str(e), error=True, sd_notify=True)
    else:
      print_line('Invalid json received, check readme for the appropriate format. Received json: ' + payload, error=True, sd_notify=True)
    pass


# Load configuration file
config_dir = parse_args.config_dir

config = ConfigParser(delimiters=('=', ), inline_comment_prefixes=('#'))
config.optionxform = str
try:
    with open(os.path.join(config_dir, 'config.ini')) as config_file:
        config.read_file(config_file)
except IOError:
    print_line('No configuration file "config.ini"', error=True, sd_notify=True)
    sys.exit(1)

reporting_mode = config['General'].get('reporting_method', 'mqtt-json')
usb_adapter = config['General'].get('usbDevice', 'ttyACM0')
numOfResends = config['Schellenberg'].get('commandResends', '9')
default_base_topic = 'miflora'

base_topic = config['MQTT'].get('base_topic', default_base_topic).lower()

# Check configuration
if reporting_mode not in ['mqtt-json']:
    print_line('Configuration parameter reporting_mode set to an invalid value', error=True, sd_notify=True)
    sys.exit(1)

print_line('Configuration accepted', console=False, sd_notify=True)

# MQTT connection
if reporting_mode in ['mqtt-json']:
    print_line('Connecting to MQTT broker ...')
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_publish = on_publish
    mqtt_client.on_message = on_message
    
    if reporting_mode == 'mqtt-json':
        mqtt_client.will_set('{}/$announce'.format(base_topic), payload='{}', retain=True)
    elif reporting_mode == 'mqtt-smarthome':
        mqtt_client.will_set('{}/connected'.format(base_topic), payload='0', retain=True)

    if config['MQTT'].getboolean('tls', False):
        # According to the docs, setting PROTOCOL_SSLv23 "Selects the highest protocol version
        # that both the client and server support. Despite the name, this option can select
        # “TLS” protocols as well as “SSL”" - so this seems like a resonable default
        mqtt_client.tls_set(
            ca_certs=config['MQTT'].get('tls_ca_cert', None),
            keyfile=config['MQTT'].get('tls_keyfile', None),
            certfile=config['MQTT'].get('tls_certfile', None),
            tls_version=ssl.PROTOCOL_SSLv23
        )

    mqtt_username = os.environ.get("MQTT_USERNAME", config['MQTT'].get('username'))
    mqtt_password = os.environ.get("MQTT_PASSWORD", config['MQTT'].get('password', None))

    if mqtt_username:
        mqtt_client.username_pw_set(mqtt_username, mqtt_password)
    try:
        mqtt_client.connect(os.environ.get('MQTT_HOSTNAME', config['MQTT'].get('hostname', 'localhost')),
                            port=int(os.environ.get('MQTT_PORT', config['MQTT'].get('port', '1883'))),
                            keepalive=config['MQTT'].getint('keepalive', 60))
    except:
        print_line('MQTT connection error. Please check your settings in the configuration file "config.ini"', error=True, sd_notify=True)
        sys.exit(1)
    else:
        mqtt_client.publish('{}/connected'.format(base_topic), payload='1', retain=True)
        mqtt_client.subscribe(base_topic)
        mqtt_client.loop_start()
        sleep(1.0) # some slack to establish the connection

sd_notifier.notify('READY=1')

print_line('Initialization complete, starting MQTT publish loop', console=True, sd_notify=True)

loop_flag=1
counter = 0
while loop_flag == 1:
    #wait for callback to occur
    sleep(0.5)
    counter += 1
    if counter % 10 == 0:
      counter = 0
      timestamp = datetime.now().isoformat()
      mqtt_client.publish('{}/heartbeat'.format(base_topic), payload=timestamp, retain=True)

#!/usr/bin/python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------
# irrigation.py für den automatischen Start eingetragen in: 
# Schauen, ob Script im Hintergrund läuft: ps aux | grep /home/raspberry/irrigation.py
# 
#
# CHANGELOG:
# 2018-12-15:
# MQTT-Anbindung für die Ventilsteuerung realisiert und initial getestet
#
# 2018-12-24:
# Anbindung an OpenHAB 2 und Benennung der Schaltungen entsprechend der OpenHAB-
# IDs
# Angepasst, dass ab sofort JSON in der Form {'valve': 1, 'pin': 4, 'state': 'ON'}
# gesendet wird. Der state kann 'ON' oder 'OFF' sein
#
# 2019-01-08:
# Status-Topic eingeführt. Aufbau: garden/irrigation/valve-%d-state
# Gibt bei geöffnetem Ventil ON und bei geschlossenem Ventil OFF zurück. Hierfür wird
# nach dem setzen eines GPIO Pins auf HIGH oder LOW geprüft, ob dieser wirklich aktuell
# den Zustand hat und dann entsprechend eine Status-Meldung verschickt.
# In /etc/rc.local für den Autostart eingetragen
# python /home/pi/irrigation.py & > /var/log/irrigation.log 2>&1
#
# 2019-01-25:
# Broker-Url auf 'house.lan' geändert
#--------------------------------------------------------------------------------

import RPi.GPIO as gpio
import paho.mqtt.client as mqtt
import json
from functools import partial

PINS     = [2, 3, 4, 9, 10]

# MQTT Broker (running on the OpenHAB Server)
BROKER_ADDRESS = '10.50.50.20'
MQTT_COMMAND_TOPIC     = 'garden/irrigation'
MQTT_VALVE_STATE_TOPIC = 'garden/irrigation/valve-{}-state'

def open(pin):
    gpio.output(pin, gpio.LOW)


def close(pin):
    gpio.output(pin, gpio.HIGH)

def onMessage(client, userdata, message):
    msg     = str(message.payload.decode("utf-8"))
    command = json.loads(msg)
    print(command)
    if 'ON' == command['state']:
        open(command['pin'])
        publishValveState(client, command['valve'], 'ON')
    elif 'OFF' == command['state']:
        close(command['pin'])
        publishValveState(client, command['valve'], 'OFF')
 
def onConnect(client, userdata, flags, rc):
    client.subscribe(MQTT_COMMAND_TOPIC, 0)
    
def publishValveState(client, valve, state):
    mqttValveStateTopic = createMqttValveStateTopic(valve)
    client.publish(mqttValveStateTopic, state)
    
def createMqttValveStateTopic(valve):
    return MQTT_VALVE_STATE_TOPIC.format(valve)

def main(prompt):
    try:
        gpio.setmode(gpio.BCM)
        gpio.setup(PINS, gpio.OUT, initial=gpio.HIGH) 

        client = mqtt.Client('irrigation')
        client.on_connect    = onConnect
        client.on_message    = onMessage
        client.connect(BROKER_ADDRESS) 
        client.loop_forever()   
        
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.unsubscribe(MQTT_COMMAND_TOPIC)
        client.disconnect()
        gpio.cleanup()  # this ensures a clean exit
        print('QUIT')

if __name__ == '__main__':
    main('Action? ')

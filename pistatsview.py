#!/usr/bin/env python
import pika
from pymongo import MongoClient
import json
import argparse
import sys
import time
import RPi.GPIO as GPIO

firstInsert = True

# Initialize database
client = MongoClient('localhost', 27017)
db = client.database
posts = db.posts

# Parse command line arguments
parser = argparse.ArgumentParser(description='')
parser.add_argument('-b', required=True)
parser.add_argument('-p')
parser.add_argument('-c')
parser.add_argument('-k', required=True)
args = parser.parse_args()

PORT_NUM = 5672
address = args.b
vHost = args.p
cred = args.c
key = args.k

# Set defaults if no argument supplied
if not vHost:
    vHost = '/'
if cred:
    user = cred.split(':')[0]
    password = cred.split(':')[1]
else:
    user = 'guest'
    password = 'guest'

# Set up connection
try:
    pika_creds = pika.PlainCredentials(user, password)
    pika_params = pika.ConnectionParameters(address, PORT_NUM, vHost, pika_creds)

    connection = pika.BlockingConnection(pika_params)
    channel = connection.channel()

    channel.exchange_declare(exchange='pi_utilization',
                             type='direct')

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='pi_utilization',
                       queue=queue_name,
                       routing_key = key)

except pika.exceptions.ChannelError as CE:
    print('ERROR: channel error has occurred')
    sys.exit(2)

except pika.exceptions.ChannelClosed as CC:
    print('ERROR: permission denied')
    sys.exit(2)

except pika.exceptions.ConnectionClosed as CC:
    print('ERROR: could not connect to channel')
    sys.exit(2)

except pika.exceptions.ProbableAuthenticationError as PAE:
    print('ERROR: login and password did not match')
    sys.exit(2)

except pika.exceptions.ProbableAccessDeniedError as PADE:
    print('ERROR: invalid virtual host')
    sys.exit(2)

print('Waiting for logs.')


# Change the GPIO output for the LED light
# depending on the utilization percentage
# that the method is passed.
def changeLight(util_percent):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(29, GPIO.OUT)
    GPIO.setup(31, GPIO.OUT)
    GPIO.setup(33, GPIO.OUT)
    # If less than 25%, light up GREEN
    if util_percent < 0.25:
        GPIO.output(29, False)
        GPIO.output(31, True)
        GPIO.output(33, False)

    # If greater than 25% and less than 50%, light up YELLOW
    elif util_percent < 0.50:
        GPIO.output(29, True)
        GPIO.output(31, True)
        GPIO.output(33, False)

    # If greater than 50%, light up RED
    else:
        GPIO.output(29, True)
        GPIO.output(31, False)
        GPIO.output(33, False)

hiLo = {}


def callback(ch, method, properties, body):
    data = json.loads(body.decode("utf-8"))

    # Store data in db
    global firstInsert
    if firstInsert:
        global hiLo
        hiLo = {
            '_id': '0',
            'cpuHi': data["cpu"],
            'cpuLo': data["cpu"],
            'lorxHi': data["net"]["lo"]["rx"],
            'lorxLo': data["net"]["lo"]["rx"],
            'lotxHi': data["net"]["lo"]["tx"],
            'lotxLo': data["net"]["lo"]["tx"],
            'ethrxHi': data["net"]["eth0"]["rx"],
            'ethrxLo': data["net"]["eth0"]["rx"],
            'ethtxHi': data["net"]["eth0"]["tx"],
            'ethtxLo': data["net"]["eth0"]["tx"],
            'wlanrxHi': data["net"]["wlan0"]["rx"],
            'wlanrxLo': data["net"]["wlan0"]["rx"],
            'wlantxHi': data["net"]["wlan0"]["tx"],
            'wlantxLo': data["net"]["wlan0"]["tx"]
        }
        firstInsert = False
        posts.insert(hiLo)
    else:
        thing = db.posts.find_one({'_id': '0'})
        if data["cpu"] > thing['cpuHi']:
            posts.update({'_id': '0'}, {"$set": {'cpuHi': data["cpu"]}})
        if data["cpu"] < thing['cpuLo']:
            posts.update({'_id': '0'}, {"$set": {'cpuLo': data["cpu"]}})
        if data["net"]["lo"]["rx"] > thing['lorxHi']:
            posts.update({'_id': '0'}, {"$set": {'lorxHi': data["net"]["lo"]["rx"]}})
        if data["net"]["lo"]["rx"] < thing['lorxLo']:
            posts.update({'_id': '0'}, {"$set": {'lorxLo': data["net"]["lo"]["rx"]}})
        if data["net"]["lo"]["tx"] > thing['lotxHi']:
            posts.update({'_id': '0'}, {"$set": {'lotxHi': data["net"]["lo"]["tx"]}})
        if data["net"]["lo"]["tx"] < thing['lotxLo']:
            posts.update({'_id': '0'}, {"$set": {'lotxLo': data["net"]["lo"]["tx"]}})
        if data["net"]["eth0"]["rx"] > thing['ethrxHi']:
            posts.update({'_id': '0'}, {"$set": {'ethrxHi': data["net"]["eth0"]["rx"]}})
        if data["net"]["eth0"]["rx"] < thing['ethrxLo']:
            posts.update({'_id': '0'}, {"$set": {'ethrxLo': data["net"]["eth0"]["rx"]}})
        if data["net"]["eth0"]["tx"] > thing['ethtxHi']:
            posts.update({'_id': '0'}, {"$set": {'ethtxHi': data["net"]["eth0"]["tx"]}})
        if data["net"]["eth0"]["tx"] < thing['ethtxLo']:
            posts.update({'_id': '0'}, {"$set": {'ethtxLo': data["net"]["eth0"]["tx"]}})
        if data["net"]["wlan0"]["rx"] > thing['wlanrxHi']:
            posts.update({'_id': '0'}, {"$set": {'wlanrxHi': data["net"]["wlan0"]["rx"]}})
        if data["net"]["wlan0"]["rx"] < thing['wlanrxLo']:
            posts.update({'_id': '0'}, {"$set": {'wlanrxLo': data["net"]["wlan0"]["rx"]}})
        if data["net"]["wlan0"]["tx"] > thing['wlantxHi']:
            posts.update({'_id': '0'}, {"$set": {'wlantxHi': data["net"]["wlan0"]["tx"]}})
        if data["net"]["wlan0"]["tx"] < thing['wlantxLo']:
            posts.update({'_id': '0'}, {"$set": {'wlantxLo': data["net"]["wlan0"]["tx"]}})

    # Echo utilization stats
    rec = posts.find_one({'_id': '0'})
    print("cpu:", data["cpu"], " [Hi:", rec['cpuHi'], ", Lo:", rec['cpuLo'], "]")
    print("lo: rx=", data["net"]["lo"]["rx"], "B/s [Hi:", rec['lorxHi'], "B/s, Lo:", rec['lorxLo'], "B/s], tx=",
          data["net"]["lo"]["tx"], "B/s [Hi: ", rec['lotxHi'], "B/s, Lo:", rec['lotxLo'], "B/s]")
    print("eth0: rx=", data["net"]["eth0"]["rx"], "B/s [Hi:", rec['ethrxHi'], "B/s, Lo:", rec['ethrxLo'],
          "B/s], tx=", data["net"]["eth0"]["tx"], "B/s [Hi:", rec['ethtxHi'], "B/s, Lo:", rec['ethtxLo'], "B/s]")
    print("wlan0: rx=", data["net"]["wlan0"]["rx"], "B/s [Hi:", rec['wlanrxHi'], "B/s, Lo:", rec['wlanrxLo'],
          "B/s], tx=", data["net"]["wlan0"]["tx"], "B/s [Hi:", rec['wlantxHi'], "B/s, Lo:", rec['wlantxLo'],
          "B/s]\n")

    # Update LED
    changeLight(data["cpu"])

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)

channel.start_consuming()
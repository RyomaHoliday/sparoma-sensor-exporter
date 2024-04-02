#!/usr/bin/env python3

import json
import os
import tinytuya
from prometheus_client import Gauge, start_http_server
import time
import sys

# Prometheusの設定
PORT = 8000
CONFIG = "devices.json"
DEBUG = False

# env variables
PORT = int(os.getenv("PORT", PORT))
CONFIG = os.getenv("CONFIG", CONFIG)
DEBUG = os.getenv("DEBUG", DEBUG)


# Gaugeの作成
labels = ['device_name', 'device_id', 'device_ip', 'device_version']
gc = Gauge('co2', 'Co2 Data from Sparoma device', labels, namespace='sparoma', subsystem='meter', unit='co2')
gt = Gauge('temperature', 'Temp Data from Sparoma device', labels, namespace='sparoma', subsystem='meter', unit='temperature')
gh = Gauge('humidity', 'Hum Data from Sparoma device', labels, namespace='sparoma', subsystem='meter', unit='humidity')

def main():
  # load configured devices
  with open(CONFIG, "r") as f:
    config = json.load(f)
  print("loaded %d devices from %s" % (len(config), CONFIG))

  devices = {}
  device = None
  for d in config:
    if d['model'] == 'PTH8':
      devices[d['id']] = d
      device = d['id']

  
  if len(devices) > 1:
    print("Too many devices configured, only one device is supported at this time")
    sys.exit(1)
  
  # Start up the server to expose the metrics.
  start_http_server(PORT)
  STATUS_TIMER = 30
  KEEPALIVE_TIMER = 12

  d = tinytuya.OutletDevice(devices[device]['id'], devices[device]['ip'], devices[device]['key'], persist=True, version=devices[device]['version'])
  if DEBUG:
    print(" > Send Request for Status < ")
  data = d.status()
  if data and 'Err' in data:
    print("Status request returned an error, is version %r and local key %r correct?" % (d.version, d.local_key))
    sys.exit(1)
  
  heartbeat_time = time.time() + KEEPALIVE_TIMER
  status_time = time.time() + STATUS_TIMER

  while(True):
    if status_time and time.time() >= status_time:
      # get status
      data = d.status().get('dps', {})
      if DEBUG:
        print(data)
      status_time = time.time() + STATUS_TIMER
      heartbeat_time = time.time() + KEEPALIVE_TIMER
      # set the metrics
      label_values = [devices[device]['product_name'], devices[device]['id'], devices[device]['ip'], devices[device]['version']]
      if '2' in data:
        gc.labels(*label_values).set(data['2'])
      else:
        gc.remove(*label_values)
      if '18' in data:
        gt.labels(*label_values).set(data['18'])
      else:
        gt.remove(*label_values)
      if '19' in data:
        gh.labels(*label_values).set(data['19'])
      else:
        gh.remove(*label_values)
    elif time.time() >= heartbeat_time:
        # send a keep-alive
        data = d.heartbeat(nowait=False)
        heartbeat_time = time.time() + KEEPALIVE_TIMER
    else:
      # no need to send anything, just listen for an asynchronous update
      data = d.receive()

    if data and 'Err' in data:
      if DEBUG:
        print("Received error!")
      # rate limit retries so we don't hammer the device
      time.sleep(5)

if __name__ == '__main__':
  main()

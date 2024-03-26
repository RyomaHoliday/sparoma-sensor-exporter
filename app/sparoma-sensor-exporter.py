#!/usr/bin/env python3

import tinytuya
from prometheus_client import Gauge, start_http_server
import time
import sys

# tinytuyaの設定
DEVICE_IP = 'Auto'

# Prometheusの設定
PROMETHEUS_PORT = 8000

# Gaugeの作成
g1 = Gauge('co2', 'Co2 Data from Sparoma device', ['device_id'], namespace='sparoma', subsystem='meter', unit='co2')
g2 = Gauge('temperature', 'Temp Data from Sparoma device', ['device_id'], namespace='sparoma', subsystem='meter', unit='temperature')
g3 = Gauge('humidity', 'Hum Data from Sparoma device', ['device_id'], namespace='sparoma', subsystem='meter', unit='humidity')

def main():
  # Start up the server to expose the metrics.
  start_http_server(PROMETHEUS_PORT)
  STATUS_TIMER = 30
  KEEPALIVE_TIMER = 12
  d = tinytuya.OutletDevice(DEVICE_ID, DEVICE_IP, DEVICE_KEY, persist=True)

  print(" > Send Request for Status < ")
  data = d.status()
  if data and 'Err' in data:
      print("Status request returned an error, is version %r and local key %r correct?" % (d.version, d.local_key))
      sys.exit(1)

  heartbeat_time = time.time() + KEEPALIVE_TIMER
  status_time = time.time() + STATUS_TIMER

  while(True):
    if status_time and time.time() >= status_time:
        # update dps
        d.updatedps()
        # get status
        data = d.status().get('dps', {})
        print(data)
        status_time = time.time() + STATUS_TIMER
        heartbeat_time = time.time() + KEEPALIVE_TIMER
        # set the metrics
        g1.labels(device_id=DEVICE_ID).set(data.get('2', 0))
        g2.labels(device_id=DEVICE_ID).set(data.get('18', 0))
        g3.labels(device_id=DEVICE_ID).set(data.get('19', 0))
    elif time.time() >= heartbeat_time:
        # send a keep-alive
        data = d.heartbeat(nowait=False)
        heartbeat_time = time.time() + KEEPALIVE_TIMER
    else:
        # no need to send anything, just listen for an asynchronous update
        data = d.receive()

    if data and 'Err' in data:
        print("Received error!")
        # rate limit retries so we don't hammer the device
        time.sleep(5)

if __name__ == '__main__':
  if len(sys.argv) < 3:
    if len(sys.argv) < 2:
        print("Error: Device ID is missing.")
    else:
        print("Error: Device key is missing.")
    sys.exit(1)

  DEVICE_ID = sys.argv[1]
  DEVICE_KEY = sys.argv[2]
  main()

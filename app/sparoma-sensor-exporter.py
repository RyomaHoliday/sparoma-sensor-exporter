#!/usr/bin/env python3

import json
import os
import sys
import time
import logging
from typing import Dict, Any, Optional

import tinytuya
from prometheus_client import Gauge, start_http_server


class SparomaExporter:
    """Prometheus exporter for Sparoma PTH-8 sensors."""
    
    def __init__(self):
        self.port = int(os.getenv("PORT", 8000))
        self.config_path = os.getenv("CONFIG", "devices.json")
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        
        # Timer settings
        self.status_timer = 30
        self.keepalive_timer = 12
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if self.debug else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Prometheus metrics
        self.labels = ['device_name', 'device_id', 'device_ip', 'device_version']
        self.co2_gauge = Gauge(
            'co2', 'Co2 Data from Sparoma device', 
            self.labels, namespace='sparoma', subsystem='meter', unit='co2'
        )
        self.temperature_gauge = Gauge(
            'temperature', 'Temp Data from Sparoma device', 
            self.labels, namespace='sparoma', subsystem='meter', unit='temperature'
        )
        self.humidity_gauge = Gauge(
            'humidity', 'Hum Data from Sparoma device', 
            self.labels, namespace='sparoma', subsystem='meter', unit='humidity'
        )
        
        self.device_config: Optional[Dict[str, Any]] = None
        self.device: Optional[tinytuya.OutletDevice] = None

    def load_config(self) -> Dict[str, Any]:
        """Load device configuration from JSON file."""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            self.logger.info(f"Loaded {len(config)} devices from {self.config_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file {self.config_path} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)
    
    def find_pth8_device(self, config: list) -> Dict[str, Any]:
        """Find and validate PTH8 device configuration."""
        pth8_devices = [d for d in config if d.get('model') == 'PTH8']
        
        if len(pth8_devices) == 0:
            self.logger.error("No PTH8 devices found in configuration")
            sys.exit(1)
        elif len(pth8_devices) > 1:
            self.logger.error("Multiple PTH8 devices found. Only one device is supported.")
            sys.exit(1)
        
        return pth8_devices[0]
    
    def setup_device(self) -> tinytuya.OutletDevice:
        """Initialize Tuya device connection."""
        device = tinytuya.OutletDevice(
            self.device_config['id'],
            self.device_config['ip'],
            self.device_config['key'],
            persist=True,
            version=self.device_config['version']
        )
        
        # Test initial connection
        self.logger.debug("Testing initial device connection")
        data = device.status()
        if data and 'Err' in data:
            self.logger.error(
                f"Status request returned an error. Check version {device.version} "
                f"and local key {device.local_key}"
            )
            sys.exit(1)
        
        return device
    
    def update_metrics(self, data: Dict[str, Any]):
        """Update Prometheus metrics with sensor data."""
        label_values = [
            self.device_config['product_name'],
            self.device_config['id'],
            self.device_config['ip'],
            self.device_config['version']
        ]
        
        # CO2 data (data point '2')
        if '2' in data:
            self.co2_gauge.labels(*label_values).set(data['2'])
        else:
            self.co2_gauge.remove(*label_values)
        
        # Temperature data (data point '18')
        if '18' in data:
            self.temperature_gauge.labels(*label_values).set(data['18'])
        else:
            self.temperature_gauge.remove(*label_values)
        
        # Humidity data (data point '19')
        if '19' in data:
            self.humidity_gauge.labels(*label_values).set(data['19'])
        else:
            self.humidity_gauge.remove(*label_values)
    
    def run(self):
        """Main execution loop."""
        # Load configuration
        config = self.load_config()
        self.device_config = self.find_pth8_device(config)
        
        # Setup device
        self.device = self.setup_device()
        
        # Start Prometheus HTTP server
        start_http_server(self.port)
        self.logger.info(f"Prometheus metrics server started on port {self.port}")
        
        # Initialize timers
        heartbeat_time = time.time() + self.keepalive_timer
        status_time = time.time() + self.status_timer
        
        # Main monitoring loop
        while True:
            try:
                if time.time() >= status_time:
                    # Get status data
                    data = self.device.status().get('dps', {})
                    self.logger.debug(f"Device status: {data}")
                    
                    # Update metrics
                    self.update_metrics(data)
                    
                    # Reset timers
                    status_time = time.time() + self.status_timer
                    heartbeat_time = time.time() + self.keepalive_timer
                    
                elif time.time() >= heartbeat_time:
                    # Send keep-alive
                    self.device.heartbeat(nowait=False)
                    heartbeat_time = time.time() + self.keepalive_timer
                    
                else:
                    # Listen for asynchronous updates
                    data = self.device.receive()
                    if data and 'Err' in data:
                        self.logger.warning("Received error from device")
                        time.sleep(5)  # Rate limit retries
                        
            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(5)


def main():
    """Entry point."""
    exporter = SparomaExporter()
    exporter.run()


if __name__ == '__main__':
    main()

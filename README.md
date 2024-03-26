# sparoma-sensor-exporter
Sparoma's PTH-8 sensor for Prometheus Exporter

## Metrics

* CO2  
* Temperature  
* Humidity  

## Install  

```bash
# run with su
mkdir /opt/sparoma-sensor-exporter
python3 -m venv /opt/sparoma-sensor-exporter/.venv
/opt/sparoma-sensor-exporter/.venv/bin/pip install -r ./sparoma-sensor-exporter/app/requirements.txt
cp ./sparoma-sensor-exporter/app/sparoma-sensor-exporter.py /opt/sparoma-sensor-exporter/
chmod 744 /opt/sparoma-sensor-exporter/sparoma-sensor-exporter.py
```

## systemd

```bash
cp ./systemd/sparoma-sensor-exporter.service /etc/systemd/system/sparoma-sensor-exporter.service
systemctl daemon-reload
systemctl start sparoma-sensor-exporter
```


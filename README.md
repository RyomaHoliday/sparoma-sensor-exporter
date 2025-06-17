# sparoma-sensor-exporter
Sparoma's PTH-8 sensor for Prometheus Exporter

## Metrics

* CO2  
* Temperature  
* Humidity  

## デバイス設定

TinyTuyaをインストールして設定ファイルを生成します：

```bash
pip install tinytuya
python -m tinytuya wizard
```

詳細: https://github.com/jasonacox/tinytuya

生成された`devices.json`を`devices.json.example`を参考に適切に配置します。

## Docker での実行（推奨）

### 基本実行

```bash
# devices.jsonを作成
cp devices.json.example devices.json
# 実際のデバイス情報を編集
nano devices.json

# コンテナをビルドして実行
docker-compose up --build
```

### Prometheus + Grafana監視スタック付きで実行

```bash
docker-compose --profile monitoring up --build
```

アクセス先：
- Sparoma Exporter: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### 環境変数

- `PORT`: HTTPサーバーポート（デフォルト: 8000）
- `CONFIG`: devices.jsonファイルのパス（デフォルト: /app/devices.json）
- `DEBUG`: デバッグログの有効化（デフォルト: false）

## 従来のインストール方法

### Python環境で直接実行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
CONFIG=devices.json DEBUG=true python3 app/sparoma-sensor-exporter.py
```

### systemdサービスとしてインストール

```bash
# root権限で実行
mkdir /opt/sparoma-sensor-exporter
python3 -m venv /opt/sparoma-sensor-exporter/.venv
/opt/sparoma-sensor-exporter/.venv/bin/pip install -r ./app/requirements.txt
cp ./app/sparoma-sensor-exporter.py /opt/sparoma-sensor-exporter/
cp ./devices.json /opt/sparoma-sensor-exporter/
chmod 744 /opt/sparoma-sensor-exporter/sparoma-sensor-exporter.py

# systemd設定
cp ./systemd/sparoma-sensor-exporter.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable sparoma-sensor-exporter
systemctl start sparoma-sensor-exporter
```


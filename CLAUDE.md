# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Sparoma PTH-8センサー用のPrometheusエクスポーター。TinyTuyaライブラリを使用してTuya互換のスマートセンサーからCO2、温度、湿度データを収集し、Prometheusメトリクスとして公開する。

## アーキテクチャ

- **メインアプリケーション**: `app/sparoma-sensor-exporter.py` - センサーデータを継続的にポーリングするシングルスレッドPythonデーモン
- **デバイス設定**: TinyTuyaウィザードで生成される`devices.json`が必要（リポジトリには含まれない）
- **デプロイメント**: `/opt/sparoma-sensor-exporter/`の仮想環境でsystemdサービスとして動作するよう設計

## 主要コンポーネント

- Tuya IoTデバイスとの通信に`tinytuya`ライブラリを使用
- ポート8000でPrometheusメトリクスを公開（PORT環境変数で設定可能）
- デバイス接続のためのハートビート機構（12秒）とステータスポーリング（30秒）を実装
- デバイスデータポイントのマッピング: `'2'` → CO2、`'18'` → 温度、`'19'` → 湿度
- 現在はインスタンスあたり1つのPTH-8デバイスのみサポート

## 開発コマンド

### Docker（推奨）
```bash
# 基本実行
docker-compose up --build

# 監視スタック付き実行
docker-compose --profile monitoring up --build

# コンテナのみビルド
docker build -t sparoma-sensor-exporter .
```

### Python環境での開発
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt

# ローカル実行（devices.jsonが必要）
CONFIG=devices.json PORT=8000 DEBUG=true python3 app/sparoma-sensor-exporter.py
```

### デバイス設定のセットアップ
```bash
# TinyTuyaをインストールしてウィザードを実行してdevices.jsonを生成
pip install tinytuya
python -m tinytuya wizard
```

## 設定

- **PORT**: HTTPサーバーポート（デフォルト: 8000）
- **CONFIG**: devices.jsonファイルのパス（デフォルト: "devices.json"）
- **DEBUG**: デバッグログの有効化（デフォルト: False）

## Prometheusメトリクス

すべてのメトリクスは名前空間`sparoma`、サブシステム`meter`を使用：
- `sparoma_meter_co2_co2` - CO2レベル
- `sparoma_meter_temperature_temperature` - 温度測定値
- `sparoma_meter_humidity_humidity` - 湿度測定値

各メトリクスには以下のラベルが含まれる：`device_name`、`device_id`、`device_ip`、`device_version`
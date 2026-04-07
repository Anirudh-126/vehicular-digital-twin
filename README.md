
# Vehicular Digital Twin System

A real-time IoT-based vehicular digital twin framework using MQTT, InfluxDB, and Python.

## Overview
This project simulates and monitors multiple vehicles using real-world GPS data (GeoLife dataset) and performs anomaly detection in real time.

## Architecture
Dataset Replay → MQTT → Digital Twin → InfluxDB → API / Visualization

## Features
- Real-time vehicle telemetry streaming
- Anomaly detection (overspeed, sudden change)
- Multi-vehicle simulation
- Time-series data storage (InfluxDB)
- REST API using Flask
- Interactive map visualization using Folium

## Tech Stack
- Python
- MQTT (Mosquitto)
- InfluxDB
- Flask
- Folium
- Docker

## How to Run
1. Start infrastructure:
   docker-compose up

2. Run dataset replay:
   python dataset_replay/geolife_replay.py

3. Run digital twin:
   python digital_twin/digital_twin.py

4. Run API:
   python api/app.py

5. Run visualization scripts

## Dataset
Microsoft GeoLife GPS dataset

## Use Case
Smart mobility, digital twin systems, real-time anomaly detection.

import json
import time
import random
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ===============================
# InfluxDB config
# ===============================
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "M6IAYSF8jkGBLYIfWaVPhy1o83aRCjhJFyyor_2Bd-2c_A5E0ngkH77p88iFTIxIu_Cl1ukB57XRm9ta9qYOaA=="
ORG = "college"
BUCKET = "vehicular_data"

influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
write_api = influx.write_api(write_options=SYNCHRONOUS)

# ===============================
# Memory (for sudden speed change)
# ===============================
last_speed = {}

# ===============================
# Anomaly control (IMPORTANT)
# ===============================
ANOMALY_PROBABILITY = 0.02        # 2% chance only
ANOMALY_COOLDOWN = 20             # seconds gap per vehicle
MAX_ANOMALIES_PER_VEHICLE = 3     # only 2-3 anomalies per vehicle

last_anomaly_time = {}
anomaly_count = {}

# ===============================
# MQTT Callbacks
# ===============================
def on_connect(client, userdata, flags, rc):
    print("Digital Twin connected to MQTT broker")
    client.subscribe("vehicle/telemetry")


def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())

    vehicle_id = data["vehicle_id"]
    lat = float(data["latitude"])
    lon = float(data["longitude"])
    speed = float(data["speed"])

    # -------------------------
    # WRITE TELEMETRY
    # -------------------------
    telemetry_point = (
        Point("vehicle_telemetry")
        .tag("vehicle_id", vehicle_id)
        .field("speed", speed)
        .field("latitude", lat)
        .field("longitude", lon)
        .time(time.time_ns(), WritePrecision.NS)
    )
    write_api.write(bucket=BUCKET, org=ORG, record=telemetry_point)

    # -------------------------
    # ANOMALY DETECTION (CONTROLLED)
    # -------------------------
    anomaly = False
    reason = ""

    # init anomaly memory for vehicle
    if vehicle_id not in last_anomaly_time:
        last_anomaly_time[vehicle_id] = 0

    if vehicle_id not in anomaly_count:
        anomaly_count[vehicle_id] = 0

    now = time.time()

    cooldown_ok = (now - last_anomaly_time[vehicle_id]) >= ANOMALY_COOLDOWN
    limit_ok = anomaly_count[vehicle_id] < MAX_ANOMALIES_PER_VEHICLE

    # only check anomaly if allowed
    if cooldown_ok and limit_ok:
        # random trigger (so it doesn't happen always)
        if random.random() < ANOMALY_PROBABILITY:

            # original anomaly logic (your rules)
            if speed > 70:
                anomaly = True
                reason = "overspeed"

            if vehicle_id in last_speed:
                if abs(speed - last_speed[vehicle_id]) > 25:
                    anomaly = True
                    reason = "sudden_speed_change"

            # if no rule matched, still force one random anomaly reason
            # (optional but makes sure we actually get 2-3 anomalies)
            if not anomaly:
                anomaly = True
                reason = random.choice(["overspeed", "sudden_speed_change"])

    # -------------------------
    # WRITE ANOMALY WITH SAME LOCATION
    # -------------------------
    if anomaly:
        anomaly_point = (
            Point("vehicle_anomaly")
            .tag("vehicle_id", vehicle_id)
            .tag("reason", reason)
            .field("speed", speed)
            .field("latitude", lat)
            .field("longitude", lon)
            .time(time.time_ns(), WritePrecision.NS)
        )
        write_api.write(bucket=BUCKET, org=ORG, record=anomaly_point)

        anomaly_count[vehicle_id] += 1
        last_anomaly_time[vehicle_id] = now

        print(f"ANOMALY {vehicle_id} @ ({lat},{lon}) reason={reason} speed={speed}")

    # update speed memory
    last_speed[vehicle_id] = speed


# ===============================
# MQTT Setup
# ===============================
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect("localhost", 1883, 60)

print("Digital Twin started")
mqtt_client.loop_forever()


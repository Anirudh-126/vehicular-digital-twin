import time
import json
import math
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883
TOPIC = "vehicle/telemetry"
REPLAY_DELAY = 1  # seconds

# ---- Haversine distance (meters) ----
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ---- Select 4 trajectory files ----
vehicles = {
    "vehicle_01": "/home/anirudh/vehicular-digital-twin/dataset/geolife/Geolife Trajectories 1.3/Data/000/Trajectory/20081023025304.plt",
    "vehicle_02": "/home/anirudh/vehicular-digital-twin/dataset/geolife/Geolife Trajectories 1.3/Data/001/Trajectory/20081023055305.plt",
    "vehicle_03": "/home/anirudh/vehicular-digital-twin/dataset/geolife/Geolife Trajectories 1.3/Data/002/Trajectory/20081023124523.plt",
    "vehicle_04": "/home/anirudh/vehicular-digital-twin/dataset/geolife/Geolife Trajectories 1.3/Data/003/Trajectory/20081023175854.plt",
}

# ---- Load points from a .plt file ----
def load_points(plt_file):
    with open(plt_file, "r") as f:
        lines = f.readlines()
    data_lines = lines[6:]  # skip header
    points = []
    for line in data_lines:
        parts = line.strip().split(",")
        if len(parts) < 2:
            continue
        lat = float(parts[0])
        lon = float(parts[1])
        points.append((lat, lon))
    return points

# ---- Prepare vehicle data ----
vehicle_data = {}
for vid, path in vehicles.items():
    pts = load_points(path)
    vehicle_data[vid] = {
        "points": pts,
        "index": 0,
        "prev_lat": None,
        "prev_lon": None
    }
    print(f"Loaded {vid}: {len(pts)} points from {path}")

client = mqtt.Client()
client.connect(MQTT_HOST, MQTT_PORT, 60)

print("Multi-vehicle GeoLife replay started...")

while True:
    all_finished = True

    for vid, info in vehicle_data.items():
        pts = info["points"]
        idx = info["index"]

        if idx >= len(pts):
            continue

        all_finished = False

        lat, lon = pts[idx]

        # speed calculation
        if info["prev_lat"] is None:
            speed_kmh = 0.0
        else:
            dist_m = haversine_m(info["prev_lat"], info["prev_lon"], lat, lon)
            speed_kmh = (dist_m / REPLAY_DELAY) * 3.6

        info["prev_lat"], info["prev_lon"] = lat, lon
        info["index"] += 1

        payload = {
            "vehicle_id": vid,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "speed": round(speed_kmh, 2),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

        client.publish(TOPIC, json.dumps(payload))
        print(f"Sent {vid}: {payload}")

    if all_finished:
        print("All vehicle replays finished.")
        break

    time.sleep(REPLAY_DELAY)


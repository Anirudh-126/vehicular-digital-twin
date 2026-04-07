import json
import time
import random
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("localhost", 1883, 60)

vehicles = {
    "vehicle_01": {"lat": 12.9716, "lon": 77.5946, "dlat": 0.00012, "dlon": 0.00010, "speed": 40},
    "vehicle_02": {"lat": 12.9750, "lon": 77.6000, "dlat": -0.00010, "dlon": 0.00014, "speed": 45},
    "vehicle_03": {"lat": 12.9690, "lon": 77.5900, "dlat": 0.00015, "dlon": -0.00012, "speed": 38},
}

print("City-wide vehicle simulator started")

while True:
    for vid, v in vehicles.items():

        # Move vehicle smoothly
        v["lat"] += v["dlat"]
        v["lon"] += v["dlon"]

        # Normal speed drift
        v["speed"] += random.uniform(-2, 2)

        # Keep speed realistic
        v["speed"] = max(20, min(v["speed"], 65))

        # 🔴 RANDOM ANOMALY INJECTION (5% chance)
        if random.random() < 0.05:
            v["speed"] = random.uniform(75, 90)  # overspeed event

        data = {
            "vehicle_id": vid,
            "latitude": round(v["lat"], 6),
            "longitude": round(v["lon"], 6),
            "speed": round(v["speed"], 2),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

        client.publish("vehicle/telemetry", json.dumps(data))
        print(f"Sent {vid}: {data}")

    time.sleep(2)


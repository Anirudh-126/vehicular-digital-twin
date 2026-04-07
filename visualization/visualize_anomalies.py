from influxdb_client import InfluxDBClient
import folium

# ---------------- InfluxDB Config ----------------
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "M6IAYSF8jkGBLYIfWaVPhy1o83aRCjhJFyyor_2Bd-2c_A5E0ngkH77p88iFTIxIu_Cl1ukB57XRm9ta9qYOaA=="
ORG = "college"
BUCKET = "vehicular_data"

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=ORG
)

query_api = client.query_api()

# ---------------- Query Anomalies ----------------
anomaly_query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "vehicle_anomaly")
'''

anomaly_tables = query_api.query(anomaly_query, org=ORG)

# ---------------- Create Map ----------------
m = folium.Map(location=[12.9716, 77.5946], zoom_start=13)

for table in anomaly_tables:
    for record in table.records:
        vehicle_id = record["vehicle_id"]
        speed = record["_value"]

        # ---------------- Fetch Latest Telemetry ----------------
        telemetry_query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -1h)
          |> filter(fn: (r) => r._measurement == "vehicle_telemetry")
          |> filter(fn: (r) => r.vehicle_id == "{vehicle_id}")
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 3)
        '''

        telemetry_tables = query_api.query(telemetry_query, org=ORG)

        lat = None
        lon = None

        for t in telemetry_tables:
            for r in t.records:
                if r["_field"] == "latitude":
                    lat = r["_value"]
                elif r["_field"] == "longitude":
                    lon = r["_value"]

        if lat and lon:
            folium.Marker(
                location=[lat, lon],
                popup=f"""
                🚨 ANOMALY<br>
                Vehicle: {vehicle_id}<br>
                Speed: {speed}
                """,
                icon=folium.Icon(color="red", icon="warning")
            ).add_to(m)

# ---------------- Save Map ----------------
m.save("vehicle_anomalies.html")
print("Anomaly map saved as vehicle_anomalies.html")


from influxdb_client import InfluxDBClient
import folium
import pandas as pd

# -------- InfluxDB Configuration --------
INFLUX_URL = "http://localhost:8086"
TOKEN = "M6IAYSF8jkGBLYIfWaVPhy1o83aRCjhJFyyor_2Bd-2c_A5E0ngkH77p88iFTIxIu_Cl1ukB57XRm9ta9qYOaA=="
ORG = "college"
BUCKET = "vehicular_data"

# -------- Connect to InfluxDB --------
client = InfluxDBClient(
    url=INFLUX_URL,
    token=TOKEN,
    org=ORG
)

query_api = client.query_api()

# -------- Flux Query --------
query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "vehicle_telemetry")
  |> filter(fn: (r) => r._field == "latitude" or r._field == "longitude")
'''
anomaly_query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "vehicle_anomaly")
  |> filter(fn: (r) => r._field == "speed")
'''

anomaly_tables = query_api.query(anomaly_query)
tables = query_api.query(query)

# -------- Convert to DataFrame --------
records = []
for table in tables:
    for row in table.records:
        records.append({
            "time": row.get_time(),
            "vehicle_id": row.values["vehicle_id"],
            "field": row.get_field(),
            "value": row.get_value()
        })

df = pd.DataFrame(records)

anomaly_records = []
for table in anomaly_tables:
    for row in table.records:
        anomaly_records.append({
            "time": row.get_time(),
            "vehicle_id": row.values["vehicle_id"],
            "speed": row.get_value()
        })

anomaly_df = pd.DataFrame(anomaly_records)
# Pivot latitude & longitude
df = df.pivot_table(
    index=["time", "vehicle_id"],
    columns="field",
    values="value"
).reset_index()

# -------- Create Map --------
map_center = [df["latitude"].mean(), df["longitude"].mean()]
m = folium.Map(location=map_center, zoom_start=14)

colors = {
    "vehicle_01": "red",
    "vehicle_02": "blue",
    "vehicle_03": "green"
}

# -------- Plot Paths --------
for vehicle_id, group in df.groupby("vehicle_id"):
    points = list(zip(group["latitude"], group["longitude"]))

    folium.PolyLine(
        points,
        color=colors.get(vehicle_id, "black"),
        weight=4,
        tooltip=vehicle_id
    ).add_to(m)
# -------- Plot Anomaly Markers --------
for _, anomaly in anomaly_df.iterrows():
    vehicle_data = df[df["vehicle_id"] == anomaly["vehicle_id"]]

    if not vehicle_data.empty:
        lat = vehicle_data.iloc[-1]["latitude"]
        lon = vehicle_data.iloc[-1]["longitude"]

        folium.Marker(
            location=[lat, lon],
            popup=(
                f"⚠️ Anomaly<br>"
                f"Vehicle: {anomaly['vehicle_id']}<br>"
                f"Speed: {anomaly['speed']}"
            ),
            icon=folium.Icon(color="red", icon="warning")
        ).add_to(m)

# -------- Save Map --------
m.save("vehicle_paths_with_anomalies.html")

print("Vehicle path map generated: vehicle_paths.html")

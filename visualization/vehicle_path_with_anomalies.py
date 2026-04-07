from influxdb_client import InfluxDBClient
import folium

# ===============================
# InfluxDB Config
# ===============================
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

# ===============================
# VEHICLE COLORS (Easy to Explain)
# ===============================
vehicle_colors = {
    "vehicle_01": "blue",
    "vehicle_02": "green",
    "vehicle_03": "orange"
}

# ===============================
# QUERY VEHICLE PATHS
# ===============================
path_query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "vehicle_telemetry")
  |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
  |> keep(columns: ["_time","vehicle_id","latitude","longitude"])
'''

path_tables = query_api.query(path_query)

vehicle_paths = {}

for table in path_tables:
    for row in table.records:
        vid = row["vehicle_id"]
        lat = row["latitude"]
        lon = row["longitude"]

        if vid not in vehicle_paths:
            vehicle_paths[vid] = []

        vehicle_paths[vid].append((lat, lon))

# ===============================
# QUERY ANOMALIES
# ===============================
anomaly_query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "vehicle_anomaly")
  |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
  |> keep(columns: ["_time","vehicle_id","latitude","longitude","speed","reason"])
'''

anomaly_tables = query_api.query(anomaly_query)

anomalies = []

for table in anomaly_tables:
    for row in table.records:
        anomalies.append({
            "vehicle_id": row["vehicle_id"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "speed": row["speed"],
            "reason": row["reason"] if "reason" in row.values else "unknown",
            "time": row["_time"]
        })

# ===============================
# CREATE MAP
# ===============================
if not vehicle_paths:
    print("No vehicle data found")
    exit()

# Use first vehicle first coordinate to center map
first_vehicle = next(iter(vehicle_paths))
center_location = vehicle_paths[first_vehicle][0]

m = folium.Map(
    location=center_location,
    zoom_start=13
)

# ===============================
# DRAW VEHICLE PATHS
# ===============================
for vid, coords in vehicle_paths.items():
    color = vehicle_colors.get(vid, "black")

    folium.PolyLine(
        coords,
        color=color,
        weight=4,
        tooltip=f"{vid} Path"
    ).add_to(m)

# ===============================
# ADD ANOMALY MARKERS
# ===============================
for anomaly in anomalies:
    folium.Marker(
        location=[anomaly["latitude"], anomaly["longitude"]],
        icon=folium.Icon(color="red", icon="warning-sign"),
        popup=f"""
        🚨 Anomaly Detected<br>
        Vehicle: {anomaly['vehicle_id']}<br>
        Speed: {anomaly['speed']}<br>
        Reason: {anomaly['reason']}<br>
        Time: {anomaly['time']}
        """
    ).add_to(m)

# ===============================
# LEGEND (Very Important for Presentation)
# ===============================
legend_html = """
<div style="
position: fixed; 
bottom: 50px; left: 50px; width: 200px; height: 140px; 
background-color: white;
border:2px solid grey; 
z-index:9999; 
font-size:14px;
padding:10px;
">
<b>Vehicle Legend</b><br>
<span style="color:blue;">●</span> Vehicle 01<br>
<span style="color:green;">●</span> Vehicle 02<br>
<span style="color:purple;">●</span> Vehicle 03<br>
<span style="color:orange;">●</span> Vehicle 04<br>
<span style="color:red;">●</span> Anomaly
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

# ===============================
# SAVE MAP
# ===============================
m.save("vehicle_path_with_anomalies.html")
print("Map generated: vehicle_path_with_anomalies.html")

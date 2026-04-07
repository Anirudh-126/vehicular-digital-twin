from flask import Flask, jsonify
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "M6IAYSF8jkGBLYIfWaVPhy1o83aRCjhJFyyor_2Bd-2c_A5E0ngkH77p88iFTIxIu_Cl1ukB57XRm9ta9qYOaA=="
ORG = "college"
BUCKET = "vehicular_data"

app = Flask(__name__)

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=ORG
)

query_api = client.query_api()

@app.route("/vehicle/<vehicle_id>/latest", methods=["GET"])
def get_latest_vehicle_data(vehicle_id):
    query = f'''
    from(bucket: "{BUCKET}")
      |> range(start: -10m)
      |> filter(fn: (r) => r._measurement == "vehicle_telemetry")
      |> last()
    '''

    result = query_api.query(org=ORG, query=query)

    response = {}
    for table in result:
        for record in table.records:
            response[record.get_field()] = record.get_value()
            response["time"] = record.get_time().isoformat()
            response["vehicle_id"] = vehicle_id

    if not response:
        return jsonify({"error": "No data found"}), 404

    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

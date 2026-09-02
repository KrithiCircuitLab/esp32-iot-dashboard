"""
Project 3: Smart RFID IoT Dashboard
Author: Krithiga Ramesh (KrithiCircuitLab)

WHAT THIS DOES:
├── Subscribes to MQTT broker (broker.hivemq.com)
├── Receives RFID scan events from ESP32
├── Receives potentiometer sensor data
├── Serves live web dashboard on port 5000
└── Shows real-time access log and sensor graph

HOW TO RUN:
    pip install paho-mqtt flask
    python dashboard.py
    Open browser: http://localhost:5000

C firmware sends:
    RFID topic:   {"card_id":"83F81EFC","access":"GRANTED"}
    Sensor topic: {"potentiometer":2048}
"""

import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

# ═══════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════
MQTT_BROKER   = "broker.hivemq.com"
MQTT_PORT     = 1883
TOPIC_RFID    = "krithicircuitlab/rfid"
TOPIC_SENSOR  = "krithicircuitlab/sensor"
TOPIC_COMMAND = "krithicircuitlab/command"
TOPIC_STATUS  = "krithicircuitlab/status"

# ═══════════════════════════════════════════
# SHARED DATA STORE
# ═══════════════════════════════════════════
data_store = {
    "rfid_events":    [],
    "sensor_history": [],
    "device_status":  "offline",
    "total_scans":    0,
    "granted_count":  0,
    "denied_count":   0,
}
data_lock = threading.Lock()

# ═══════════════════════════════════════════
# FLASK WEB APP
# ═══════════════════════════════════════════
app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>KrithiCircuitLab — RFID IoT Dashboard</title>
    <meta http-equiv="refresh" content="3">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 20px;
            border-bottom: 1px solid #30363d;
            margin-bottom: 20px;
        }
        .header h1 { color: #58a6ff; font-size: 28px; }
        .header p  { color: #8b949e; margin-top: 5px; }
        .status-dot {
            display: inline-block;
            width: 10px; height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .online  { background: #3fb950; }
        .offline { background: #f85149; }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .card h3 {
            color: #8b949e;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .card .value {
            font-size: 36px;
            font-weight: bold;
            color: #58a6ff;
            margin-top: 10px;
        }
        .card.granted .value { color: #3fb950; }
        .card.denied  .value { color: #f85149; }

        .section {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .section h2 {
            color: #58a6ff;
            margin-bottom: 15px;
            font-size: 16px;
        }

        table { width: 100%; border-collapse: collapse; }
        th {
            color: #8b949e;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 8px;
            border-bottom: 1px solid #30363d;
            text-align: left;
        }
        td {
            padding: 10px 8px;
            border-bottom: 1px solid #21262d;
            font-size: 14px;
        }
        .badge {
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge.granted { background: #1a3a1a; color: #3fb950; }
        .badge.denied  { background: #3a1a1a; color: #f85149; }

        .sensor-bar-container {
            background: #0d1117;
            border-radius: 10px;
            height: 30px;
            margin: 10px 0;
            overflow: hidden;
        }
        .sensor-bar {
            height: 100%;
            background: linear-gradient(90deg, #58a6ff, #3fb950);
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        .sensor-value {
            font-size: 24px;
            font-weight: bold;
            color: #58a6ff;
            margin-top: 10px;
        }

        .control-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            margin: 5px;
        }
        .btn-green {
            background: #1a3a1a;
            color: #3fb950;
            border: 1px solid #3fb950;
        }
        .btn-red {
            background: #3a1a1a;
            color: #f85149;
            border: 1px solid #f85149;
        }
        .footer {
            text-align: center;
            color: #8b949e;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔐 RFID IoT Dashboard</h1>
        <p>
            <span class="status-dot {{ 'online' if status == 'online' else 'offline' }}"></span>
            ESP32 Device: <strong>{{ status.upper() }}</strong>
            &nbsp;|&nbsp;
            Last updated: {{ now }}
        </p>
    </div>

    <!-- Stats Cards -->
    <div class="grid">
        <div class="card">
            <h3>Total Scans</h3>
            <div class="value">{{ total }}</div>
        </div>
        <div class="card granted">
            <h3>Access Granted</h3>
            <div class="value">{{ granted }}</div>
        </div>
        <div class="card denied">
            <h3>Access Denied</h3>
            <div class="value">{{ denied }}</div>
        </div>
    </div>

    <!-- Potentiometer -->
    <div class="section">
        <h2>📊 Potentiometer Sensor</h2>
        <div class="sensor-value">
            {{ sensor_pct }}%
            <span style="font-size:14px;color:#8b949e">
                (raw: {{ sensor_raw }})
            </span>
        </div>
        <div class="sensor-bar-container">
            <div class="sensor-bar" style="width: {{ sensor_pct }}%"></div>
        </div>
    </div>

    <!-- Remote Control -->
    <div class="section">
        <h2>🎮 Remote Control (ESP32 LEDs)</h2>
        <button class="control-btn btn-green"
            onclick="sendCmd('LED_GREEN')">
            🟢 Green LED ON
        </button>
        <button class="control-btn btn-red"
            onclick="sendCmd('LED_RED')">
            🔴 Red LED ON
        </button>
        <script>
        function sendCmd(cmd) {
            fetch('/send_command?cmd=' + cmd)
                .then(r => r.json())
                .then(d => console.log(d));
        }
        </script>
    </div>

    <!-- Access Log -->
    <div class="section">
        <h2>📋 Access Log (Last 20 events)</h2>
        <table>
            <tr>
                <th>Time</th>
                <th>Card UID</th>
                <th>Status</th>
                <th>Scan #</th>
            </tr>
            {% for event in events %}
            <tr>
                <td>{{ event.time }}</td>
                <td><code>{{ event.uid }}</code></td>
                <td>
                    <span class="badge {{ 'granted' if event.authorized else 'denied' }}">
                        {{ 'GRANTED' if event.authorized else 'DENIED' }}
                    </span>
                </td>
                <td>#{{ event.scan_count }}</td>
            </tr>
            {% endfor %}
            {% if not events %}
            <tr>
                <td colspan="4"
                    style="text-align:center;color:#8b949e;padding:30px">
                    No scans yet — scan an RFID card!
                </td>
            </tr>
            {% endif %}
        </table>
    </div>

    <div class="footer">
        KrithiCircuitLab | ESP32 RFID IoT Dashboard |
        Auto-refreshes every 3 seconds
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    with data_lock:
        events = list(reversed(data_store["rfid_events"][-20:]))
        sensor = data_store["sensor_history"]
        last_sensor = sensor[-1] if sensor else {"raw": 0, "percentage": 0}

    return render_template_string(
        DASHBOARD_HTML,
        status     = data_store["device_status"],
        total      = data_store["total_scans"],
        granted    = data_store["granted_count"],
        denied     = data_store["denied_count"],
        events     = events,
        sensor_raw = last_sensor["raw"],
        sensor_pct = last_sensor["percentage"],
        now        = datetime.now().strftime('%H:%M:%S')
    )

@app.route('/api/data')
def api_data():
    """JSON API endpoint for external tools."""
    with data_lock:
        return jsonify({
            "status":  data_store["device_status"],
            "total":   data_store["total_scans"],
            "granted": data_store["granted_count"],
            "denied":  data_store["denied_count"],
            "events":  data_store["rfid_events"][-10:],
            "sensor":  data_store["sensor_history"][-10:],
        })

@app.route('/send_command')
def send_command():
    """Send LED command to ESP32 via MQTT."""
    cmd = request.args.get('cmd', '')
    if cmd in ['LED_GREEN', 'LED_RED']:
        if mqtt_client_instance:
            mqtt_client_instance.publish(TOPIC_COMMAND, cmd, qos=1)
        return jsonify({"sent": cmd})
    return jsonify({"error": "invalid command"})

# ═══════════════════════════════════════════
# MQTT CLIENT
# ═══════════════════════════════════════════
mqtt_client_instance = None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ MQTT connected to {MQTT_BROKER}")
        client.subscribe(TOPIC_RFID)
        client.subscribe(TOPIC_SENSOR)
        client.subscribe(TOPIC_STATUS)
        print(f"📡 Subscribed to:")
        print(f"   {TOPIC_RFID}")
        print(f"   {TOPIC_SENSOR}")
        print(f"   {TOPIC_STATUS}")

        # Force device online when MQTT connects
        with data_lock:
            data_store["device_status"] = "online"
        print(f"   📡 Device: ONLINE")
    else:
        print(f"❌ MQTT connection failed: rc={rc}")

def on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode('utf-8')

    print(f"[{datetime.now().strftime('%H:%M:%S')}] {topic}: {payload}")

    try:
        data = json.loads(payload)

        with data_lock:

            # ── RFID event received ──────────────────────────
            if topic == TOPIC_RFID:
                # C firmware sends: {"card_id":"83F81EFC","access":"GRANTED"}
                is_granted = data.get("access", "DENIED") == "GRANTED"

                event = {
                    "time":       datetime.now().strftime('%H:%M:%S'),
                    "uid":        data.get("card_id", "UNKNOWN"),
                    "authorized": is_granted,
                    "scan_count": data_store["total_scans"] + 1,
                }

                data_store["rfid_events"].append(event)
                data_store["total_scans"] += 1

                if is_granted:
                    data_store["granted_count"] += 1
                    print(f"   🟢 GRANTED: {event['uid']}")
                else:
                    data_store["denied_count"] += 1
                    print(f"   🔴 DENIED:  {event['uid']}")

                # Keep only last 100 events
                if len(data_store["rfid_events"]) > 100:
                    data_store["rfid_events"].pop(0)

            # ── Sensor data received ─────────────────────────
            elif topic == TOPIC_SENSOR:
                # C firmware sends: {"potentiometer":2048}
                raw_val = data.get("potentiometer", 0)
                percentage = round((raw_val * 100) / 4095)

                reading = {
                    "time":       datetime.now().strftime('%H:%M:%S'),
                    "raw":        raw_val,
                    "percentage": percentage,
                }

                data_store["sensor_history"].append(reading)
                print(f"   📊 Sensor: {percentage}% (raw: {raw_val})")

                if len(data_store["sensor_history"]) > 100:
                    data_store["sensor_history"].pop(0)

            # ── Device status received ───────────────────────
            elif topic == TOPIC_STATUS:
                status = data.get("status", "unknown")
                data_store["device_status"] = status
                print(f"   📡 Device: {status.upper()}")

    except json.JSONDecodeError as e:
        print(f"   ⚠️  JSON parse error: {e}")
        print(f"   Raw payload: {payload}")

def on_disconnect(client, userdata, rc):
    print(f"⚠️  MQTT disconnected (rc={rc})")
    with data_lock:
        data_store["device_status"] = "offline"

def start_mqtt():
    """Start MQTT client in background thread."""
    global mqtt_client_instance

    mqtt_client_instance = mqtt.Client(
        client_id="KrithiDashboard_" + str(int(datetime.now().timestamp()))
    )

    mqtt_client_instance.on_connect    = on_connect
    mqtt_client_instance.on_message    = on_message
    mqtt_client_instance.on_disconnect = on_disconnect

    print(f"🔌 Connecting to MQTT: {MQTT_BROKER}:{MQTT_PORT}")

    mqtt_client_instance.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client_instance.loop_forever()

# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═"*55)
    print("  RFID IoT Dashboard")
    print("  Author: Krithiga Ramesh | KrithiCircuitLab")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═"*55)
    print(f"\n📋 MQTT Broker:  {MQTT_BROKER}:{MQTT_PORT}")
    print(f"🌐 Dashboard:    http://localhost:5000")
    print(f"📡 RFID topic:   {TOPIC_RFID}")
    print(f"📡 Sensor topic: {TOPIC_SENSOR}")
    print(f"\nC firmware JSON format expected:")
    print(f'   RFID:   {{"card_id":"83F81EFC","access":"GRANTED"}}')
    print(f'   Sensor: {{"potentiometer":2048}}')
    print(f"\nPress Ctrl+C to stop\n")

    # Start MQTT in background thread
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()

    # Start Flask dashboard
    app.run(host='0.0.0.0', port=5000, debug=False)
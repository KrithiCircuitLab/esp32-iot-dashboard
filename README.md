# ESP32 RFID IoT Dashboard

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![ESP32](https://img.shields.io/badge/Hardware-ESP32-blue)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![MQTT](https://img.shields.io/badge/Protocol-MQTT-orange)
![Flask](https://img.shields.io/badge/Dashboard-Flask-red)
![License](https://img.shields.io/badge/License-MIT-green)

A production-grade smart RFID access control system built on ESP32 — 
publishing real-time data over MQTT to a live Python web dashboard.

---

## What this project demonstrates

- RFID card scanning via RC522 (SPI protocol at register level)
- Real-time MQTT publishing to HiveMQ public broker
- Live web dashboard with Flask showing access logs
- Potentiometer sensor data streaming every 5 seconds
- Remote LED control from browser to physical hardware via MQTT
- Access granted/denied logic with authorized card management
- FreeRTOS task architecture for concurrent hardware operations
- Full IoT stack: C firmware → MQTT → Python → Web browser

---

## System architecture

```
RC522 RFID Reader (SPI)
        │
        ▼
ESP32 Firmware (C / ESP-IDF / FreeRTOS)
        │ MQTT publish over WiFi
        ▼
HiveMQ Public Broker (broker.hivemq.com:1883)
        │ MQTT subscribe
        ▼
Python Dashboard (Flask + paho-mqtt)
        │ HTTP
        ▼
Live Web Dashboard (http://localhost:5000)
        │ MQTT command publish
        ▼
ESP32 LED Control (GPIO25 / GPIO26)
```

---

## Hardware components

| Component | Interface | GPIO Pins |
|-----------|-----------|-----------|
| RC522 RFID module | SPI | MOSI:23, MISO:19, CLK:18, SS:5, RST:27 |
| Potentiometer | ADC | GPIO34 |
| Green LED | GPIO | GPIO25 |
| Red LED | GPIO | GPIO26 |

---

## Wiring diagram

```
RC522 RFID Module        ESP32 Dev Board
─────────────────        ───────────────
SDA  ──────────────────► GPIO5  (SS)
SCK  ──────────────────► GPIO18 (CLK)
MOSI ──────────────────► GPIO23 (MOSI)
MISO ◄──────────────────GPIO19 (MISO)
RST  ──────────────────► GPIO27 (RST)
VCC  ──────────────────► 3V3
GND  ──────────────────► GND

Potentiometer            ESP32 Dev Board
─────────────            ───────────────
Left pin  ─────────────► 3V3
Middle pin ────────────► GPIO34 (ADC)
Right pin ─────────────► GND

Green LED ─── 220Ω ───► GPIO25
Red LED   ─── 220Ω ───► GPIO26
```

---

## MQTT topics

| Topic | Direction | Payload example |
|-------|-----------|-----------------|
| `krithicircuitlab/rfid` | ESP32 → Dashboard | `{"card_id":"83F81EFC","access":"GRANTED"}` |
| `krithicircuitlab/sensor` | ESP32 → Dashboard | `{"potentiometer":2048}` |
| `krithicircuitlab/status` | ESP32 → Dashboard | `{"status":"online"}` |
| `krithicircuitlab/command` | Dashboard → ESP32 | `LED_GREEN` or `LED_RED` |

---

## Dashboard features

- **Live access log** — last 20 RFID scan events with timestamp, card UID, and status
- **Stats counters** — total scans, granted count, denied count
- **Sensor bar** — real-time potentiometer reading as percentage bar
- **Remote control** — Green LED and Red LED buttons control physical ESP32 hardware
- **Device status** — online/offline indicator
- **Auto-refresh** — dashboard updates every 3 seconds

---

## How to run

### Step 1 — Flash ESP32 firmware

```bash
cd firmware/
idf.py set-target esp32
idf.py build
idf.py -p COM3 flash monitor
```

### Step 2 — Install Python requirements

```bash
pip install paho-mqtt flask
```

### Step 3 — Start dashboard

```bash
python dashboard.py
```

### Step 4 — Open browser

```
http://localhost:5000
```

### Step 5 — Scan RFID card

Hold any RFID card or key fob near the RC522 reader.
Watch the live dashboard update in real time.

---

## Adding authorized cards

When an unknown card is scanned, Serial Monitor shows:

```
Card detected: A1B2C3D4
ACCESS DENIED
```

Add the UID to the firmware:

```c
#define AUTHORIZED_CARD "A1B2C3D4"
```

Rebuild and reflash — that card will now show ACCESS GRANTED
and trigger the green LED.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Firmware | C / ESP-IDF v5.5.4 |
| RTOS | FreeRTOS |
| RFID driver | Custom SPI register-level driver (rc522.c) |
| IoT protocol | MQTT (paho-mqtt) |
| Broker | HiveMQ public broker (free, no account) |
| Dashboard | Python Flask |
| Frontend | HTML / CSS / JavaScript |

---

## Key technical concepts

**Why MQTT over HTTP for IoT?**
MQTT uses a publish-subscribe model — devices publish once, all subscribers receive instantly. HTTP requires constant polling which wastes bandwidth and battery. For IoT devices publishing sensor data every few seconds, MQTT reduces bandwidth by up to 60x compared to HTTP polling.

**Why SPI for RC522?**
RC522 supports SPI, I2C, and UART. SPI is fastest and most reliable for RFID — reading card UID requires precise timing. The driver communicates directly with RC522 registers over SPI without using any third-party RFID library, demonstrating hardware-level embedded understanding.

**Why FreeRTOS?**
Real IoT devices must do multiple things simultaneously — scan RFID cards, read sensors, maintain WiFi connection, handle MQTT messages. FreeRTOS tasks run concurrently with priority scheduling, ensuring no single operation blocks the others.

---

## Project series

This is Project 3 of a 3-part embedded firmware portfolio:

| Project | Description | Link |
|---------|-------------|------|
| Project 1 | ESP32 Firmware Validation Suite | [esp32-firmware-validation-suite](https://github.com/KrithiCircuitLab/esp32-firmware-validation-suite) |
| Project 2 | ESP32 OTA Update System | [esp32-ota-update-system](https://github.com/KrithiCircuitLab/esp32-ota-update-system) |
| Project 3 | ESP32 RFID IoT Dashboard | **This repository** |

---

## Author

**Krithiga Ramesh** — Embedded Firmware & Validation Engineer  
Singapore 🇸🇬

[![GitHub](https://img.shields.io/badge/GitHub-KrithiCircuitLab-black)](https://github.com/KrithiCircuitLab)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Krithiga_Ramesh-blue)](https://linkedin.com/in/krithigaramesh-930826100)

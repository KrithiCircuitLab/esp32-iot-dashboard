# ESP32 IoT Dashboard

ESP32 based IoT sensor node publishing real-time 
data to AWS IoT Core via MQTT over TLS — with 
live web dashboard.

## Architecture
ESP32 (C/FreeRTOS)
│ MQTT over TLS (port 8883)
▼
AWS IoT Core
│ Lambda trigger
▼
Python data processor
│ REST API
▼
Web Dashboard

# Features
- FreeRTOS multitasking (sensor, WiFi, display tasks)
- MQTT over TLS (secure communication)
- AWS IoT Core integration
- Real-time web dashboard
- OTA firmware update capability
- Deep sleep power optimization

## Tech Stack
- ESP32 / ESP-IDF
- FreeRTOS
- C firmware
- Python (cloud side)
- AWS IoT Core
- MQTT

## Status
🚧 Active development

## Author
Krithiga Ramesh — Embedded Firmware Engineer
Singapore 🇸🇬

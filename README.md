# iot_parking_lot

This project is a microservice-based IoT system for managing smart parking lots. It uses MQTT and REST to connect and control sensors, gates, timers, and user services such as booking, payment, and real-time monitoring.

## 🚗 Project Features
- Real-time parking space detection via sensors
- Entrance/Exit gate management with Temporary Identification Code (TIC)
- REST API for booking and payments
- MQTT-based messaging for status updates
- Telegram Bot for user interaction
- Google Maps + ThingSpeak integration for visualization

## 🔧 Technologies Used
- Python 3
- Flask / FastAPI (REST APIs)
- MQTT (Paho-MQTT)
- JSON for configuration
- ThingSpeak
- Google Maps API
- Telegram Bot API

## 🗂️ Repository Structure
- smart-parking-lot/
├── config/              # JSON configuration files
├── devices/             # Sensor and gate simulators
├── services/            # REST/MQTT backend microservices
├── frontend/            # UI, map, ThingSpeak, display logic
├── integration/         # Broker config and system wiring
├── tests/               # Unit and integration tests
└── README.md

## 📡 Microservices Overview
| Service | Description |
|--------|-------------|
| `parking_control` | Central service registry (REST + JSON config) |
| `entrance_device` | Issues TIC and assigns parking spot (MQTT) |
| `onspot_sensor` | Publishes parking spot status (MQTT) |
| `exit_device` | Validates payment and triggers gate open |
| `timer_control` | Monitors duration of parking |
| `payment_service` | Handles payment confirmation via REST |
| `telegram_bot` | Interface for booking and alerts |
| `display_screen` | Shows availability using REST |
| `thingSpeak_adapter` | Uploads data to ThingSpeak |

## 👥 Team Members
	•	Peichun Jiang (s330592)
	•	Yudie Ren (s324480)
	•	Chunhui Liu (s328187)
	•	Jun Wei (s328962)
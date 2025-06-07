# iot_parking_lot

This project is a microservice-based IoT system for managing smart parking lots. It uses MQTT and REST to connect and control sensors, gates, timers, and user services such as booking, payment, and real-time monitoring.

## 🚗 Project Features

- REST API for Catalog
- MQTT-based messaging for status updates
- Telegram Bot for user interaction of reserve/pay

## 🔧 Technologies Used
- Python 3
- HTTP
- MQTT (Paho-MQTT)
- JSON for configuration
- Telegram Bot API

## 🗂️ Repository Structure
```bash
smart-parking-lot/
├── README.md
│
├── config/              # JSON configuration files
│   ├── devices.json
│   └── settings.json
│
├── devices/             # Sensor and gate simulators
│   ├── entrance_scanner.py
│   ├── entrance_gate.py
│   └── exit_scanner.py
│   └── exit_gate.py
│
├── src/            # REST/MQTT backend microservices
│   ├── ControlCenter.py          ## central logic/controller of system
│   ├── ManagementInterface.py	  ## Interface for the Parking device management
│   ├── Catalog.py				  ## Catalog
│   └── telegram_bot.py			  ## Telegram bot
```

## 📡 Microservices Overview
| Service | Description |
|--------|-------------|
| `ControlCenter` | Central service registry (REST + MQTT) |
| `entrance_scanner` | Scanner the palte_license and send to ControlCenter (MQTT) |
| `entrance_gate` | Open the gate and send timestamp to ControlCenter (MQTT) |
| `exit_scanner` | Scanner the palte_license and send to ControlCenter (MQTT) |
| `exit_gate` | Open the gate and send timestamp to ControlCenter (MQTT) |
| `Catalog` | Central device registry (REST) |
| `telegram_bot` | Interface for booking and payment |

## 🛠️ Getting Started

1. Clone the repo:
   ```bash
   git clone https://github.com/FindekanoChaldea/iot_parking_lot.git
   cd smart-parking-lot

## 👥 Team Members
	•	Peichun Jiang (s330592)
	•	Yudie Ren (s324480)
	•	Chunhui Liu (s328187)
	•	Jun Wei (s328962)

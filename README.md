# Centralized Log Error Counter (AWS CloudWatch + MQTT + ESP32)

A production-grade, college-level cloud monitoring system that queries AWS CloudWatch Logs, aggregates error metrics over rolling time windows, displays analytics on a dark-themed React dashboard, and broadcasts error counts via MQTT to an ESP32 microcontroller driving a TM1637 7-segment hardware display.

---

## 🏗 Architecture Overview

```
   ┌────────────────────────────────────────┐
   │            AWS CloudWatch              │
   │  Log Group: /centralized-log-error-    │
   │             counter                    │
   │  Log Stream: demo-stream               │
   └───────────────────┬────────────────────┘
                       │ Boto3 (IAM / STS)
                       ▼
   ┌────────────────────────────────────────┐
   │         FastAPI Python Backend         │
   │  - CloudWatch Log Filter & Aggregator  │
   │  - 5-Minute Bucket Timeline Generator  │
   │  - Paho-MQTT Publisher Client          │
   └──────────┬──────────────────┬──────────┘
              │ REST API         │ MQTT (Port 1883)
              ▼                  ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│ React 18 + Vite Dashboard │ │  HiveMQ Public Broker     │
│ - Recharts Error Timeline │ │  broker.hivemq.com        │
│ - Live Error Log Terminal │ └─────────────┬─────────────┘
│ - Auto-Refresh (10s-60s)  │               │ Subscribe
│ - Diagnostics & Controls  │               ▼
└───────────────────────────┘ ┌───────────────────────────┐
                              │  ESP32 Microcontroller    │
                              │  - Wokwi Hardware Sim     │
                              │  - TM1637 4-Digit Display │
                              │  - Alert Flasher LED      │
                              └───────────────────────────┘
```

---

## 🚀 Quickstart Guide

### 1. Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Install dependencies
python -m pip install -r requirements.txt

# Configure your AWS credentials
# Copy .env.example to .env and fill in your keys
notepad .env

# Run standalone CLI error counter test
python error_counter.py

# Start FastAPI server
python -m uvicorn main:app --reload --port 8000
```

The backend API documentation is available interactively at:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

### 2. Frontend Setup

```powershell
# Navigate to frontend directory
cd frontend

# Install Node modules
npm.cmd install

# Start Vite development server
npm.cmd run dev
```

Open `http://localhost:5173` in your browser. The dashboard connects to the backend through the Vite reverse proxy automatically.

---

### 3. ESP32 + TM1637 Display (Wokwi Simulation)

1. Open [https://wokwi.com](https://wokwi.com) and start a new **ESP32** project.
2. Paste `esp32_wokwi/sketch.ino` into the code editor.
3. Paste `esp32_wokwi/diagram.json` into the diagram tab.
4. Add libraries in Wokwi Library Manager: `TM1637Display`, `PubSubClient`, `ArduinoJson`.
5. Click **Start Simulation**.
6. Whenever new errors appear in CloudWatch or you click **Sync to ESP32** on the dashboard, the 7-segment display updates live!

---

## 🔑 AWS Configuration & Credentials

Edit `backend/.env`:

```ini
# AWS Region (default: us-east-1)
AWS_REGION=us-east-1

# Standard AWS IAM Credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# For AWS Academy / Learner Labs (Temporary Credentials):
AWS_SESSION_TOKEN=your_session_token_here

# Target CloudWatch Log Group & Stream
LOG_GROUP_NAME=/centralized-log-error-counter
LOG_STREAM_NAME=demo-stream

# MQTT Broker Settings
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_TOPIC=centralized/logs/error-count
```

> **Note on Security**: Never commit `.env` containing actual keys to version control. Credentials are read strictly on the server and are never exposed to frontend code.

---

## 🧪 CloudWatch Sample Log Generator

To test the system end-to-end with realistic AWS CloudWatch log data:

```powershell
# In backend/ folder:
python generate_sample_logs.py
```

This utility automatically:
1. Verifies/creates `/centralized-log-error-counter` in CloudWatch.
2. Verifies/creates `demo-stream`.
3. Injects sample `[INFO]`, `[WARNING]`, and `[ERROR]` logs with current UTC timestamps.
4. Immediately verifies with `error_counter.py`.

---

## 📡 Backend API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service uptime and system health check. |
| `GET` | `/api/aws/status` | STS caller identity & CloudWatch connection verification. |
| `GET` | `/api/logs/errors` | Total ERROR count from last `hours` (default: 1 hour). |
| `GET` | `/api/logs/recent` | Recent ERROR log events with timestamps and messages. |
| `GET` | `/api/logs/timeline` | 5-minute bucketed time-series error count for Recharts. |
| `GET` | `/api/mqtt/status` | Current HiveMQ MQTT broker connection state. |
| `POST` | `/api/mqtt/publish` | Broadcasts current error count to ESP32 display via MQTT. |

---

## 📁 Repository Structure

```
CC P-2/
├── backend/
│   ├── .env.example            # Environment variables template
│   ├── .env                    # Local credentials (ignored)
│   ├── requirements.txt        # Python package dependencies
│   ├── config.py               # Pydantic/dotenv settings manager
│   ├── cloudwatch_service.py   # Boto3 CloudWatch logs aggregator
│   ├── mqtt_service.py         # Paho-MQTT publisher client
│   ├── main.py                 # FastAPI web server & endpoints
│   ├── error_counter.py        # Standalone CLI error counter script
│   └── generate_sample_logs.py # Utility to inject realistic AWS test logs
├── frontend/
│   ├── package.json            # React + Vite dependencies
│   ├── vite.config.js          # Vite config & API reverse proxy
│   ├── index.html              # HTML shell
│   └── src/
│       ├── App.jsx             # Main dashboard UI
│       ├── App.css             # Cyberpunk/Cloud dark theme styles
│       ├── main.jsx            # React root mount
│       └── components/
│           ├── MetricCard.jsx    # Metric tile component
│           ├── TimelineChart.jsx # Recharts AreaChart
│           ├── LogViewer.jsx     # Terminal log viewer with search
│           └── AwsStatusModal.jsx# AWS diagnostics modal
└── esp32_wokwi/
    ├── sketch.ino              # Arduino C++ ESP32 firmware
    ├── diagram.json            # Wokwi simulation circuit layout
    └── README.md               # Simulation instructions
```

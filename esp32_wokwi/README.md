# ESP32 + TM1637 Display Wokwi Simulation Guide

This folder contains the complete simulation firmware and circuit configuration for the **ESP32 + TM1637 4-digit 7-segment hardware error display**.

---

## 1. Pin Connections

| ESP32 Pin | TM1637 / Component Pin | Description | Wire Color |
|---|---|---|---|
| **3V3** | **VCC** | 3.3V Power Supply | Red |
| **GND** | **GND** | Common Ground | Black |
| **GPIO 22** | **CLK** | Clock Signal | Orange |
| **GPIO 23** | **DIO** | Data Input/Output | Green |
| **GPIO 2** | **LED Anode** (via 220Ω resistor) | Error Alert Flasher | Blue |

---

## 2. Running in Wokwi (Web Browser)

1. Open [https://wokwi.com](https://wokwi.com) and click **Start New Project** -> **ESP32**.
2. Select **C++ / Arduino**.
3. In the code editor tab (`sketch.ino`), copy and paste the code from [sketch.ino](sketch.ino).
4. In the `diagram.json` tab, replace the contents with [diagram.json](diagram.json).
5. In the **Libraries** tab (Library Manager), install these 3 libraries:
   - `TM1637Display`
   - `PubSubClient`
   - `ArduinoJson`
6. Click the green **Play / Start Simulation** button.

---

## 3. How It Works

1. The ESP32 connects to `Wokwi-GUEST` WiFi (simulated network with internet access).
2. It connects to the public HiveMQ MQTT broker at `broker.hivemq.com:1883`.
3. It subscribes to the topic `centralized/logs/error-count`.
4. When the Python backend or dashboard publishes a new error count (e.g. `{"error_count": 4}`):
   - The TM1637 display updates immediately (e.g. `0004`).
   - If error count > 0, the Alert LED blinks to signal an active incident.
   - If error count == 0, the display shows `0000` and the LED remains off.

---

## 4. Manual Test using MQTT CLI or Python

You can test the simulated display from any terminal by publishing directly:

```bash
# Using python from backend/
python -c "
import paho.mqtt.client as mqtt, json
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='test-pub')
c.connect('broker.hivemq.com', 1883)
c.publish('centralized/logs/error-count', json.dumps({'error_count': 7}))
c.disconnect()
print('Dispatched count 7 to ESP32!')
"
```

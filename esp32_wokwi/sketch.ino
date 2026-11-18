/*
 * Centralized Log Error Counter - ESP32 + TM1637 Display Firmware
 * 
 * Hardware:
 *   - ESP32 Development Board
 *   - TM1637 4-Digit 7-Segment Display (CLK: GPIO 22, DIO: GPIO 23)
 *   - Alert LED (GPIO 2, built-in)
 * 
 * Network & MQTT:
 *   - WiFi: Wokwi-GUEST (no password needed in Wokwi simulator)
 *   - MQTT Broker: broker.hivemq.com:1883
 *   - MQTT Topic : centralized/logs/error-count
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <TM1637Display.h>
#include <ArduinoJson.h>

// Pin Definitions
#define CLK_PIN 22
#define DIO_PIN 23
#define ALERT_LED_PIN 2

// WiFi Credentials (Wokwi-GUEST is used by Wokwi virtual simulator)
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// MQTT Settings
const char* mqtt_broker = "broker.hivemq.com";
const int   mqtt_port   = 1883;
const char* mqtt_topic  = "centralized/logs/error-count";

// Hardware objects
TM1637Display display(CLK_PIN, DIO_PIN);
WiFiClient espClient;
PubSubClient client(espClient);

int current_error_count = 0;
unsigned long last_blink_time = 0;
bool led_state = false;

// Custom segments for TM1637 "Err " display
const uint8_t SEG_ERR[] = {
  SEG_A | SEG_D | SEG_E | SEG_F | SEG_G, // E
  SEG_E | SEG_G,                         // r
  SEG_E | SEG_G,                         // r
  0                                      // blank
};

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n==================================================");
  Serial.println("  CENTRALIZED LOG ERROR COUNTER - ESP32 FIRMWARE  ");
  Serial.println("==================================================");

  pinMode(ALERT_LED_PIN, OUTPUT);
  digitalWrite(ALERT_LED_PIN, LOW);

  // Initialize TM1637 Display (brightness 0-7)
  display.setBrightness(7);
  display.clear();
  display.showNumberDec(0, true, 4, 0); // Explicitly display 0000 across all 4 digits

  setup_wifi();

  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(mqtt_callback);
}

void setup_wifi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.print("[WiFi] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Connection timed out (check simulator connection).");
  }
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  // Convert payload buffer to String
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.println("\n--------------------------------------------------");
  Serial.print("[MQTT] Message received on topic: ");
  Serial.println(topic);
  Serial.print("[MQTT] Payload: ");
  Serial.println(message);

  int error_count = -1;

  // Try parsing as JSON object (Compatible with ArduinoJson v6 & v7)
#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<256> doc;
#endif
  DeserializationError err = deserializeJson(doc, message);

  if (!err && doc.containsKey("error_count")) {
    error_count = doc["error_count"].as<int>();
  } else {
    // If not JSON or plain number, parse integer directly
    error_count = message.toInt();
  }

  if (error_count >= 0) {
    current_error_count = error_count;
    Serial.print("[DISPLAY] Updating 7-Segment count: ");
    Serial.println(current_error_count);

    // Update TM1637 display with 4-digit leading zeros
    display.showNumberDec(current_error_count, true, 4, 0);

    // Update alert status
    if (current_error_count > 0) {
      Serial.println("[ALERT] Active errors detected in CloudWatch!");
      digitalWrite(ALERT_LED_PIN, HIGH);
    } else {
      Serial.println("[INFO] No errors reported. System normal.");
      digitalWrite(ALERT_LED_PIN, LOW);
    }
  } else {
    Serial.println("[ERROR] Unable to parse error_count from MQTT message.");
  }
  Serial.println("--------------------------------------------------");
}

void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("[MQTT] Attempting connection to ");
    Serial.print(mqtt_broker);
    Serial.print("...");

    String clientId = "ESP32-LogMonitor-" + String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println(" connected!");
      Serial.print("[MQTT] Subscribing to: ");
      Serial.println(mqtt_topic);
      client.subscribe(mqtt_topic);

      // Publish initial heartbeat
      client.publish("centralized/logs/esp32/status", "online");
    } else {
      Serial.print(" failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds...");
      delay(5000);
    }
  }
}

void loop() {
  // Ensure WiFi is connected
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  // Ensure MQTT is connected
  if (!client.connected()) {
    reconnect_mqtt();
  }

  client.loop();

  // Blink LED if active errors exist
  if (current_error_count > 0) {
    if (millis() - last_blink_time > 500) {
      last_blink_time = millis();
      led_state = !led_state;
      digitalWrite(ALERT_LED_PIN, led_state ? HIGH : LOW);
    }
  } else {
    digitalWrite(ALERT_LED_PIN, LOW);
  }

  delay(10);
}

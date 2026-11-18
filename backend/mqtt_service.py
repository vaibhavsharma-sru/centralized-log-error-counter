import json
import logging
import time
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import paho.mqtt.client as mqtt
from config import settings

logger = logging.getLogger("mqtt_service")

class MQTTService:
    def __init__(self):
        self.broker = settings.MQTT_BROKER
        self.port = settings.MQTT_PORT
        self.topic = settings.MQTT_TOPIC
        self.client_id = settings.MQTT_CLIENT_ID
        
        self.connected = False
        self.last_published_count: Optional[int] = None
        self.last_published_time: Optional[str] = None
        self.last_published_payload: Optional[Dict[str, Any]] = None
        self.client: Optional[mqtt.Client] = None
        self._initialized = False

    def ensure_connected(self, timeout: float = 3.0):
        """Lazily connects to MQTT broker and waits briefly for the connection to establish."""
        if not self._initialized or not self.client:
            self._init_client()

        start = time.time()
        while not self.connected and (time.time() - start) < timeout:
            time.sleep(0.1)

    def _init_client(self):
        try:
            self._initialized = True
            # Handle paho-mqtt 2.x CallbackAPIVersion if present
            if hasattr(mqtt, "CallbackAPIVersion"):
                self.client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id
                )
            else:
                self.client = mqtt.Client(client_id=self.client_id)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

            # Connect non-blocking
            logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}...")
            self.client.connect_async(self.broker, self.port, keepalive=30)
            self.client.loop_start()
        except Exception as e:
            logger.warning(f"Could not initialize MQTT client: {e}")
            self.connected = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = rc if isinstance(rc, int) else getattr(rc, "value", rc)
        if rc_code == 0:
            logger.info(f"Connected to MQTT Broker: {self.broker}")
            self.connected = True
        else:
            logger.warning(f"Failed to connect to MQTT Broker with code {rc_code}")
            self.connected = False

    def _on_disconnect(self, client, userdata, disconnect_flags, rc=None, properties=None):
        logger.info(f"Disconnected from MQTT Broker: {self.broker}")
        self.connected = False

    def publish_error_count(self, error_count: int, log_group: str = "") -> Dict[str, Any]:
        """
        Publishes the error count to the MQTT broker topic.
        Sends a clean JSON payload that ESP32 and dashboards can easily parse.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "error_count": int(error_count),
            "timestamp": now_iso,
            "topic": self.topic,
            "log_group": log_group or settings.LOG_GROUP_NAME,
            "unit": "last_1_hour_errors"
        }

        payload_json = json.dumps(payload)

        try:
            self.ensure_connected(timeout=3.0)

            if self.client:
                result = self.client.publish(self.topic, payload_json, qos=1)
                result.wait_for_publish(timeout=4.0)

                self.last_published_count = int(error_count)
                self.last_published_time = now_iso
                self.last_published_payload = payload

                return {
                    "success": True,
                    "broker": self.broker,
                    "topic": self.topic,
                    "error_count": int(error_count),
                    "timestamp": now_iso,
                    "payload": payload
                }
            else:
                return {
                    "success": False,
                    "error": "MQTT client not initialized",
                    "broker": self.broker,
                    "topic": self.topic
                }

        except Exception as e:
            logger.error(f"Failed to publish to MQTT topic {self.topic}: {e}")
            return {
                "success": False,
                "error": str(e),
                "broker": self.broker,
                "topic": self.topic
            }

    def get_status(self) -> Dict[str, Any]:
        """Returns the current MQTT connection status and last published info."""
        return {
            "broker": self.broker,
            "port": self.port,
            "topic": self.topic,
            "connected": self.connected,
            "last_published_count": self.last_published_count,
            "last_published_time": self.last_published_time,
            "last_payload": self.last_published_payload
        }

    def close(self):
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass

mqtt_service = MQTTService()

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

def reload_env():
    """Reloads .env dynamically so credential updates take effect immediately."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)

reload_env()

class Settings:
    @property
    def AWS_REGION(self) -> str:
        return os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

    @property
    def AWS_ACCESS_KEY_ID(self) -> str | None:
        val = os.getenv("AWS_ACCESS_KEY_ID")
        return val.strip() if val else None

    @property
    def AWS_SECRET_ACCESS_KEY(self) -> str | None:
        val = os.getenv("AWS_SECRET_ACCESS_KEY")
        return val.strip() if val else None

    @property
    def AWS_SESSION_TOKEN(self) -> str | None:
        val = os.getenv("AWS_SESSION_TOKEN")
        return val.strip() if val else None

    @property
    def LOG_GROUP_NAME(self) -> str:
        return os.getenv("LOG_GROUP_NAME", "/centralized-log-error-counter")

    @property
    def LOG_STREAM_NAME(self) -> str:
        return os.getenv("LOG_STREAM_NAME", "demo-stream")

    @property
    def MQTT_BROKER(self) -> str:
        return os.getenv("MQTT_BROKER", "broker.hivemq.com")

    @property
    def MQTT_PORT(self) -> int:
        return int(os.getenv("MQTT_PORT", 1883))

    @property
    def MQTT_TOPIC(self) -> str:
        return os.getenv("MQTT_TOPIC", "centralized/logs/error-count")

    @property
    def MQTT_CLIENT_ID(self) -> str:
        return os.getenv("MQTT_CLIENT_ID", f"cloudwatch-backend-{os.getpid()}")

    @property
    def BACKEND_PORT(self) -> int:
        return int(os.getenv("BACKEND_PORT", 8000))

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()

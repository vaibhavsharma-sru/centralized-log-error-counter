import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the backend folder
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN: str | None = os.getenv("AWS_SESSION_TOKEN")  # Common in AWS Academy / Learner Labs

    # CloudWatch Logs Configuration
    LOG_GROUP_NAME: str = os.getenv("LOG_GROUP_NAME", "/centralized-log-error-counter")
    LOG_STREAM_NAME: str = os.getenv("LOG_STREAM_NAME", "demo-stream")

    # MQTT Configuration
    MQTT_BROKER: str = os.getenv("MQTT_BROKER", "broker.hivemq.com")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC: str = os.getenv("MQTT_TOPIC", "centralized/logs/error-count")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", f"cloudwatch-backend-{os.getpid()}")

    # Server Configuration
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", 8000))
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

# Ensure backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from cloudwatch_service import cloudwatch_service
from mqtt_service import mqtt_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Centralized Log Error Counter API...")
    logger.info(f"Configured Region: {settings.AWS_REGION}")
    logger.info(f"Target Log Group: {settings.LOG_GROUP_NAME}")
    logger.info(f"Target Log Stream: {settings.LOG_STREAM_NAME}")
    logger.info(f"MQTT Broker: {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
    yield
    logger.info("Shutting down API services...")
    mqtt_service.close()

app = FastAPI(
    title="Centralized Log Error Counter API",
    description="Backend API for AWS CloudWatch Log Monitoring, Error Aggregation, and MQTT/ESP32 Publishing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class PublishRequest(BaseModel):
    error_count: Optional[int] = None

# --- API Endpoints ---

@app.get("/api/health", tags=["System"])
def get_health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "centralized-log-error-counter",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "active"
    }

@app.get("/api/aws/status", tags=["AWS CloudWatch"])
def get_aws_status():
    """Returns the AWS STS authentication & CloudWatch log group/stream connection status."""
    return cloudwatch_service.check_connection()

@app.get("/api/logs/errors", tags=["Metrics"])
def get_error_count(
    hours: int = Query(default=1, ge=1, le=168, description="Time window in hours"),
    publish_mqtt: bool = Query(default=False, description="Optionally publish the count to MQTT")
):
    """
    Counts total ERROR entries in CloudWatch Logs within the last `hours` (default 1 hr).
    Optionally auto-publishes to MQTT if `publish_mqtt=true`.
    """
    result = cloudwatch_service.count_errors(hours=hours)
    
    if publish_mqtt and result.get("success"):
        mqtt_service.publish_error_count(result["error_count"])

    return result

@app.get("/api/logs/recent", tags=["Metrics"])
def get_recent_error_logs(
    hours: int = Query(default=1, ge=1, le=168, description="Time window in hours"),
    limit: int = Query(default=50, ge=1, le=200, description="Max number of logs to return")
):
    """Retrieves actual recent ERROR log events from CloudWatch."""
    return cloudwatch_service.fetch_error_logs(hours=hours, limit=limit)

@app.get("/api/logs/timeline", tags=["Metrics"])
def get_error_timeline(
    hours: int = Query(default=1, ge=1, le=24, description="Time window in hours"),
    bucket_minutes: int = Query(default=5, ge=1, le=60, description="Bucket interval in minutes")
):
    """Returns aggregated error count time-series data suitable for Recharts."""
    return cloudwatch_service.get_error_timeline(hours=hours, bucket_minutes=bucket_minutes)

@app.get("/api/mqtt/status", tags=["MQTT"])
def get_mqtt_status():
    """Returns connection and publishing status of the MQTT broker."""
    return mqtt_service.get_status()

@app.post("/api/mqtt/publish", tags=["MQTT"])
def publish_to_mqtt(req: Optional[PublishRequest] = None):
    """
    Manually triggers an MQTT publish of the latest error count to the ESP32.
    If error_count is not provided, queries CloudWatch for the last 1 hour count.
    """
    if req and req.error_count is not None:
        count = req.error_count
    else:
        cw_res = cloudwatch_service.count_errors(hours=1)
        count = cw_res.get("error_count", 0)

    result = mqtt_service.publish_error_count(count)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.BACKEND_PORT, reload=True)

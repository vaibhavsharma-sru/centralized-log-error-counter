import datetime
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError, EndpointConnectionError
from config import settings

logger = logging.getLogger("cloudwatch_service")

# Avoid long timeouts when searching for EC2 instance metadata locally
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ.setdefault("AWS_METADATA_SERVICE_TIMEOUT", "1")
os.environ.setdefault("AWS_METADATA_SERVICE_NUM_ATTEMPTS", "1")

# Fast fail config for network calls (3s connect timeout)
BOTO_CONFIG = Config(
    connect_timeout=3,
    read_timeout=5,
    retries={"max_attempts": 1}
)

class CloudWatchService:
    def __init__(self):
        self.region = settings.AWS_REGION
        self.log_group_name = settings.LOG_GROUP_NAME
        self.log_stream_name = settings.LOG_STREAM_NAME

    def has_credentials(self) -> bool:
        """Checks if AWS credentials exist without hanging on network metadata."""
        from config import reload_env
        reload_env()
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            return True
        try:
            session = boto3.Session()
            return session.get_credentials() is not None
        except Exception:
            return False

    def _get_boto3_kwargs(self) -> Dict[str, Any]:
        """Build credentials kwargs for boto3 client."""
        from config import reload_env
        reload_env()
        kwargs: Dict[str, Any] = {
            "region_name": settings.AWS_REGION,
            "config": BOTO_CONFIG
        }
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            if settings.AWS_SESSION_TOKEN:
                kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
        return kwargs

    def get_client(self):
        """Instantiate a boto3 CloudWatch Logs client."""
        kwargs = self._get_boto3_kwargs()
        return boto3.client("logs", **kwargs)

    def get_sts_client(self):
        """Instantiate a boto3 STS client for identity verification."""
        kwargs = self._get_boto3_kwargs()
        return boto3.client("sts", **kwargs)

    def check_connection(self) -> Dict[str, Any]:
        """
        Verifies AWS credentials, STS identity, and CloudWatch log group existence.
        Returns detailed status without throwing unhandled exceptions.
        """
        if not self.has_credentials():
            return {
                "connected": False,
                "status": "CREDENTIALS_MISSING",
                "message": "AWS credentials not found. Configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in backend/.env or your AWS CLI profile.",
                "region": self.region,
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name,
                "log_group_exists": False,
                "log_stream_exists": False,
                "credentials_type": "NONE"
            }
        
        kwargs = self._get_boto3_kwargs()
        has_explicit_keys = bool(kwargs.get("aws_access_key_id"))
        account_id = None
        arn = None

        try:
            # 1. Verify STS identity
            sts = self.get_sts_client()
            identity = sts.get_caller_identity()
            account_id = identity.get("Account")
            arn = identity.get("Arn")

            # 2. Verify CloudWatch Logs access
            logs_client = self.get_client()
            
            # Check if log group exists
            groups_resp = logs_client.describe_log_groups(
                logGroupNamePrefix=self.log_group_name,
                limit=5
            )
            found_group = any(
                g.get("logGroupName") == self.log_group_name
                for g in groups_resp.get("logGroups", [])
            )

            # Check if log stream exists if group was found
            found_stream = False
            if found_group:
                try:
                    streams_resp = logs_client.describe_log_streams(
                        logGroupName=self.log_group_name,
                        logStreamNamePrefix=self.log_stream_name,
                        limit=5
                    )
                    found_stream = any(
                        s.get("logStreamName") == self.log_stream_name
                        for s in streams_resp.get("logStreams", [])
                    )
                except Exception as stream_err:
                    logger.warning(f"Error checking log stream: {stream_err}")

            return {
                "connected": True,
                "status": "CONNECTED",
                "message": "Successfully authenticated with AWS and connected to CloudWatch Logs.",
                "region": self.region,
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name,
                "log_group_exists": found_group,
                "log_stream_exists": found_stream,
                "account_id": account_id,
                "caller_arn": arn,
                "credentials_type": "EXPLICIT_KEYS" if has_explicit_keys else "DEFAULT_CHAIN",
            }

        except (NoCredentialsError, PartialCredentialsError) as e:
            return {
                "connected": False,
                "status": "CREDENTIALS_MISSING",
                "message": "AWS credentials not found. Configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in backend/.env or your AWS CLI profile.",
                "region": self.region,
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name,
                "error_details": str(e)
            }
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "ClientError")
            msg = e.response.get("Error", {}).get("Message", str(e))
            return {
                "connected": False,
                "status": "AUTH_FAILED" if "Auth" in code or "AccessDenied" in code or "InvalidClientTokenId" in code else "ERROR",
                "message": f"AWS Error ({code}): {msg}",
                "region": self.region,
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name,
                "error_code": code,
                "error_details": msg
            }
        except EndpointConnectionError as e:
            return {
                "connected": False,
                "status": "NETWORK_ERROR",
                "message": f"Could not connect to AWS endpoint in {self.region}. Check your internet connection.",
                "region": self.region,
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name,
                "error_details": str(e)
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "UNKNOWN_ERROR",
                "message": f"Unexpected error while connecting to AWS: {str(e)}",
                "region": self.region,
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name,
                "error_details": str(e)
            }

    def fetch_error_logs(self, hours: int = 1, limit: int = 100) -> Dict[str, Any]:
        """
        Retrieves actual ERROR log events from CloudWatch from the last `hours`.
        Filters for occurrences containing ERROR, [ERROR], error, etc.
        """
        if not self.has_credentials():
            return {
                "success": False,
                "total_errors": 0,
                "events": [],
                "error_code": "CREDENTIALS_MISSING",
                "error_message": "AWS credentials not configured. Please add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to backend/.env",
                "time_window_hours": hours,
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name
            }

        now = datetime.datetime.now(datetime.timezone.utc)
        start_time = now - datetime.timedelta(hours=hours)
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(now.timestamp() * 1000)

        logs_client = self.get_client()

        # Try filtering log events
        try:
            # We filter for error patterns. CloudWatch filter pattern '?ERROR ?error ?Error ?FAIL ?Exception'
            # matches any event containing any of those terms.
            response = logs_client.filter_log_events(
                logGroupName=self.log_group_name,
                logStreamNames=[self.log_stream_name],
                filterPattern='?ERROR ?error ?Error ?FAIL ?Exception',
                startTime=start_time_ms,
                endTime=end_time_ms,
                limit=limit
            )

            raw_events = response.get("events", [])
            
            # Format events for frontend presentation
            events = []
            for ev in raw_events:
                ts_ms = ev.get("timestamp", 0)
                dt = datetime.datetime.fromtimestamp(ts_ms / 1000.0, tz=datetime.timezone.utc)
                events.append({
                    "event_id": ev.get("eventId", ""),
                    "timestamp": ts_ms,
                    "timestamp_iso": dt.isoformat(),
                    "timestamp_display": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "log_stream": ev.get("logStreamName", self.log_stream_name),
                    "message": ev.get("message", "").strip(),
                    "level": "ERROR"
                })

            # Sort most recent first
            events.sort(key=lambda x: x["timestamp"], reverse=True)

            return {
                "success": True,
                "total_errors": len(events),
                "events": events,
                "time_window_hours": hours,
                "start_time_iso": start_time.isoformat(),
                "end_time_iso": now.isoformat(),
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name
            }

        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "ClientError")
            msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"CloudWatch ClientError: {code} - {msg}")
            return {
                "success": False,
                "total_errors": 0,
                "events": [],
                "error_code": code,
                "error_message": msg,
                "time_window_hours": hours,
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name
            }
        except Exception as e:
            logger.error(f"Error fetching CloudWatch logs: {e}")
            return {
                "success": False,
                "total_errors": 0,
                "events": [],
                "error_message": str(e),
                "time_window_hours": hours,
                "log_group": self.log_group_name,
                "log_stream": self.log_stream_name
            }

    def count_errors(self, hours: int = 1) -> Dict[str, Any]:
        """
        Counts total ERROR entries in the last `hours`.
        """
        result = self.fetch_error_logs(hours=hours, limit=1000)
        return {
            "error_count": result.get("total_errors", 0),
            "success": result.get("success", False),
            "time_window_hours": hours,
            "log_group": self.log_group_name,
            "log_stream": self.log_stream_name,
            "error_message": result.get("error_message")
        }

    def get_error_timeline(self, hours: int = 1, bucket_minutes: int = 5) -> Dict[str, Any]:
        """
        Aggregates error counts into time buckets (default 5-minute intervals) for charts.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        start_time = now - datetime.timedelta(hours=hours)

        # Generate buckets
        total_minutes = hours * 60
        num_buckets = total_minutes // bucket_minutes
        
        buckets = []
        for i in range(num_buckets):
            bucket_start = start_time + datetime.timedelta(minutes=i * bucket_minutes)
            bucket_end = bucket_start + datetime.timedelta(minutes=bucket_minutes)
            buckets.append({
                "time": bucket_start.strftime("%H:%M"),
                "start_ms": int(bucket_start.timestamp() * 1000),
                "end_ms": int(bucket_end.timestamp() * 1000),
                "errors": 0
            })

        # Fetch actual error events
        logs_result = self.fetch_error_logs(hours=hours, limit=1000)
        if logs_result.get("success"):
            for event in logs_result.get("events", []):
                ts = event.get("timestamp", 0)
                for b in buckets:
                    if b["start_ms"] <= ts < b["end_ms"]:
                        b["errors"] += 1
                        break

        # Strip internal start_ms / end_ms for clean JSON
        timeline = [{"time": b["time"], "errors": b["errors"]} for b in buckets]

        return {
            "success": logs_result.get("success", False),
            "timeline": timeline,
            "total_errors": logs_result.get("total_errors", 0),
            "bucket_minutes": bucket_minutes,
            "time_window_hours": hours,
            "error_message": logs_result.get("error_message")
        }

cloudwatch_service = CloudWatchService()

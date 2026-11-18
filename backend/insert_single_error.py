#!/usr/bin/env python3
"""
Insert Single Error Utility for Live Demo
Usage:
    python insert_single_error.py "Your custom error message"
"""
import sys
import time
from pathlib import Path

# Ensure backend is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from cloudwatch_service import cloudwatch_service

def insert_error(message: str):
    print(f"Connecting to CloudWatch ({settings.AWS_REGION})...")
    conn = cloudwatch_service.check_connection()
    if not conn.get("connected"):
        print(f"[-] Error: {conn.get('message')}")
        return False

    client = cloudwatch_service.get_client()
    now_ms = int(time.time() * 1000)

    # Prefix with [ERROR] if not already present
    formatted_msg = message if "ERROR" in message.upper() else f"[ERROR] {message}"

    put_kwargs = {
        "logGroupName": settings.LOG_GROUP_NAME,
        "logStreamName": settings.LOG_STREAM_NAME,
        "logEvents": [
            {
                "timestamp": now_ms,
                "message": formatted_msg
            }
        ]
    }

    try:
        # Check sequence token if stream requires it
        resp = client.describe_log_streams(
            logGroupName=settings.LOG_GROUP_NAME,
            logStreamNamePrefix=settings.LOG_STREAM_NAME
        )
        streams = resp.get("logStreams", [])
        if streams and "uploadSequenceToken" in streams[0]:
            put_kwargs["sequenceToken"] = streams[0]["uploadSequenceToken"]

        client.put_log_events(**put_kwargs)
        print(f"[+] Successfully inserted into CloudWatch:")
        print(f"    Stream : {settings.LOG_STREAM_NAME}")
        print(f"    Message: {formatted_msg}")
        print(f"[i] Refresh your dashboard to see the count update!")
        return True
    except Exception as e:
        print(f"[-] Failed to put log event: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        custom_msg = " ".join(sys.argv[1:])
    else:
        custom_msg = "[ERROR] Live Demo: Payment gateway connection timed out after 30000ms"
    insert_error(custom_msg)

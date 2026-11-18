#!/usr/bin/env python3
"""
AWS CloudWatch Sample Log Generator
Author: Cloud Engineering Project
Description: Creates the log group (/centralized-log-error-counter) and log stream (demo-stream)
if they don't already exist, and sends realistic sample log messages including ERRORs with current timestamps.
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from cloudwatch_service import cloudwatch_service

SAMPLE_LOG_TEMPLATES = [
    ("[INFO] Microservice cluster initialized successfully in region us-east-1", "INFO"),
    ("[INFO] Health check probe passed for instance i-0a8174ef213", "INFO"),
    ("[ERROR] DatabaseConnectionError: Failed to connect to Aurora PostgreSQL replica at 10.0.4.12:5432 (timeout 30s)", "ERROR"),
    ("[INFO] GET /api/v1/inventory/items HTTP/1.1 200 OK - 42ms", "INFO"),
    ("[WARNING] High CPU utilization alert on worker-node-03: 88.4%", "WARNING"),
    ("[ERROR] PaymentGatewayException: HTTP 504 Gateway Timeout while contacting Stripe API endpoint /v1/charges", "ERROR"),
    ("[INFO] User session created: uid=usr_998124991 ip=198.51.100.22", "INFO"),
    ("[ERROR] RedisClientError: Redis connection dropped unexpectedly during pipeline execution", "ERROR"),
    ("[INFO] Batch report job completed in 14.2s", "INFO"),
    ("[ERROR] AuthorizationFailureException: Token expired or invalid signature for bearer token", "ERROR"),
    ("[ERROR] SQSDeadLetterQueue: Message id msg_8812 exceeded maximum retry attempts (5)", "ERROR"),
]

def main():
    print("=" * 65)
    print("  AWS CLOUDWATCH LOG SEED UTILITY")
    print("=" * 65)
    print(f"Log Group : {settings.LOG_GROUP_NAME}")
    print(f"Log Stream: {settings.LOG_STREAM_NAME}")
    print(f"Region    : {settings.AWS_REGION}")
    print("-" * 65)

    conn = cloudwatch_service.check_connection()
    if not conn.get("connected"):
        print(f"[-] Cannot proceed: AWS is not connected.")
        print(f"[-] Status : {conn.get('status')}")
        print(f"[-] Message: {conn.get('message')}")
        print("\nPlease update backend/.env with your AWS credentials first.")
        sys.exit(1)

    logs_client = cloudwatch_service.get_client()

    # 1. Ensure Log Group Exists
    print("[1/3] Checking Log Group...")
    try:
        logs_client.create_log_group(logGroupName=settings.LOG_GROUP_NAME)
        print(f"  [+] Created Log Group: {settings.LOG_GROUP_NAME}")
    except logs_client.exceptions.ResourceAlreadyExistsException:
        print(f"  [i] Log Group already exists: {settings.LOG_GROUP_NAME}")
    except Exception as e:
        print(f"  [-] Error ensuring log group: {e}")
        sys.exit(1)

    # 2. Ensure Log Stream Exists
    print("[2/3] Checking Log Stream...")
    try:
        logs_client.create_log_stream(
            logGroupName=settings.LOG_GROUP_NAME,
            logStreamName=settings.LOG_STREAM_NAME
        )
        print(f"  [+] Created Log Stream: {settings.LOG_STREAM_NAME}")
    except logs_client.exceptions.ResourceAlreadyExistsException:
        print(f"  [i] Log Stream already exists: {settings.LOG_STREAM_NAME}")
    except Exception as e:
        print(f"  [-] Error ensuring log stream: {e}")
        sys.exit(1)

    # 3. Put Sample Log Events
    print("[3/3] Sending sample log events to CloudWatch...")
    now_ms = int(time.time() * 1000)
    
    # Generate timestamp offsets so they span across the last 30 minutes
    log_events = []
    error_count = 0
    for i, (msg, level) in enumerate(SAMPLE_LOG_TEMPLATES):
        # Stagger by ~2-3 minutes backwards
        event_time_ms = now_ms - ((len(SAMPLE_LOG_TEMPLATES) - i) * 120 * 1000)
        log_events.append({
            "timestamp": event_time_ms,
            "message": msg
        })
        if level == "ERROR":
            error_count += 1

    try:
        # Check for sequence token if required
        put_kwargs = {
            "logGroupName": settings.LOG_GROUP_NAME,
            "logStreamName": settings.LOG_STREAM_NAME,
            "logEvents": log_events
        }
        
        # Describe streams to get uploadSequenceToken if needed
        resp = logs_client.describe_log_streams(
            logGroupName=settings.LOG_GROUP_NAME,
            logStreamNamePrefix=settings.LOG_STREAM_NAME
        )
        streams = resp.get("logStreams", [])
        if streams and "uploadSequenceToken" in streams[0]:
            put_kwargs["sequenceToken"] = streams[0]["uploadSequenceToken"]

        logs_client.put_log_events(**put_kwargs)
        print(f"  [+] Successfully pushed {len(log_events)} log events to CloudWatch!")
        print(f"  [+] Injected {error_count} ERROR logs into stream '{settings.LOG_STREAM_NAME}'.")
        print("\nYou can now run `python error_counter.py` or inspect the dashboard!")
    except Exception as e:
        print(f"  [-] Failed to put log events: {e}")
        sys.exit(1)

    print("=" * 65)

if __name__ == "__main__":
    main()

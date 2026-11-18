#!/usr/bin/env python3
"""
Centralized Log Error Counter - Standalone CLI Script
Author: Cloud Engineering Project
Description: Connects to AWS CloudWatch Logs, counts ERROR entries from the past hour,
and publishes the metric to the HiveMQ MQTT broker for ESP32 display.
"""

import sys
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from cloudwatch_service import cloudwatch_service
from mqtt_service import mqtt_service

def main():
    parser = argparse.ArgumentParser(description="Centralized Log Error Counter (AWS CloudWatch + MQTT)")
    parser.add_argument("--hours", type=int, default=1, help="Time window in hours (default: 1)")
    parser.add_argument("--publish-mqtt", action="store_true", default=True, help="Publish error count to MQTT")
    parser.add_argument("--no-mqtt", dest="publish_mqtt", action="store_false", help="Skip MQTT publishing")
    args = parser.parse_args()

    print("=" * 65)
    print("  CENTRALIZED LOG ERROR COUNTER - AWS CLOUDWATCH & MQTT")
    print("=" * 65)
    print(f"AWS Region      : {settings.AWS_REGION}")
    print(f"Log Group       : {settings.LOG_GROUP_NAME}")
    print(f"Log Stream      : {settings.LOG_STREAM_NAME}")
    print(f"Time Window     : Last {args.hours} hour(s)")
    print(f"MQTT Broker     : {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
    print(f"MQTT Topic      : {settings.MQTT_TOPIC}")
    print("-" * 65)

    # 1. Check AWS Connection
    print("[1/3] Testing AWS CloudWatch connection...")
    conn = cloudwatch_service.check_connection()
    if conn.get("connected"):
        print(f"  [+] Connected! Account ID: {conn.get('account_id') or 'N/A'}")
        print(f"  [+] Log Group Exists: {conn.get('log_group_exists')}")
        print(f"  [+] Log Stream Exists: {conn.get('log_stream_exists')}")
    else:
        print(f"  [-] AWS Connection Status: {conn.get('status')}")
        print(f"  [-] Message: {conn.get('message')}")
        if conn.get("error_details"):
            print(f"  [-] Details: {conn.get('error_details')}")
        print("\n  [TIP] Check backend/.env to configure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,")
        print("        and (if in AWS Academy / Learner Lab) AWS_SESSION_TOKEN.")
        print("-" * 65)

    # 2. Fetch and Count Errors
    print(f"[2/3] Querying CloudWatch for ERROR logs in the last {args.hours} hour(s)...")
    logs_result = cloudwatch_service.fetch_error_logs(hours=args.hours)

    total_errors = logs_result.get("total_errors", 0)
    print(f"  [+] Total Errors Found: {total_errors}")

    events = logs_result.get("events", [])
    if events:
        print("\n  Recent Error Entries:")
        print("  " + "-" * 60)
        for ev in events[:5]:
            print(f"  [{ev['timestamp_display']}] {ev['message']}")
        if len(events) > 5:
            print(f"  ... and {len(events) - 5} more error entries.")
    else:
        if logs_result.get("success"):
            print("  [i] No ERROR logs found in the selected time window.")
        else:
            print(f"  [-] Could not retrieve logs: {logs_result.get('error_message')}")

    print("-" * 65)

    # 3. Publish to MQTT
    try:
        if args.publish_mqtt:
            print(f"[3/3] Publishing error count ({total_errors}) to MQTT broker...")
            pub_result = mqtt_service.publish_error_count(total_errors)
            if pub_result.get("success"):
                print(f"  [+] Successfully published to {settings.MQTT_TOPIC} on {settings.MQTT_BROKER}!")
                print(f"  [+] ESP32 / Wokwi subscriber will now display: {total_errors}")
            else:
                print(f"  [-] MQTT publish failed: {pub_result.get('error')}")
        else:
            print("[3/3] MQTT publishing skipped (--no-mqtt flag used).")
    finally:
        mqtt_service.close()

    print("=" * 65)
    print("Done.")

if __name__ == "__main__":
    main()

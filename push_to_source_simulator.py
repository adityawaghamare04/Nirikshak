#!/usr/bin/env python3
# ============================================================
#  push_to_source_simulator.py — Pushes mock sensor data to Source Firebase
#  Endpoint: https://dht11-4ed11-default-rtdb.asia-southeast1.firebasedatabase.app/
#
#  Simulates all 5 physical sensors (Temperature, Vibration, Current, Voltage, RPM)
#  Optimized to run HTTP requests asynchronously in a thread pool to avoid network block
#  and maintain a strict 1-second delay.
# ============================================================

import time
import json
import random
import math
import urllib.request
import sys
import concurrent.futures
from datetime import datetime

# Prevent encoding crashes in Windows console when piping/printing special characters
if sys.platform.startswith('win'):
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

SOURCE_URL = "https://dht11-4ed11-default-rtdb.asia-southeast1.firebasedatabase.app"

def send_to_firebase(payload):
    try:
        headers = {"Content-Type": "application/json"}
        
        # 1. Append to /sensor/history (POST request)
        logs_url = f"{SOURCE_URL}/sensor/history.json"
        req_log = urllib.request.Request(
            logs_url,
            data=json.dumps(payload).encode(),
            method="POST",
            headers=headers
        )
        with urllib.request.urlopen(req_log, timeout=4) as response:
            res_data = json.loads(response.read().decode())
            push_id = res_data.get("name", "N/A")

        # 2. Update the latest reading states with a single PATCH request
        latest_url = f"{SOURCE_URL}/sensor/latest.json"
        req_latest = urllib.request.Request(
            latest_url,
            data=json.dumps(payload).encode(),
            method="PATCH",
            headers=headers
        )
        with urllib.request.urlopen(req_latest, timeout=4) as response:
            pass

        print(
            f"[{payload['timestamp']}] Pushed ID={push_id} | "
            f"Temp={payload['temperature']}C, Vib={payload['vibration']}g, Curr={payload['current']}A, Volt={payload['voltage']}V, RPM={payload['rpm']}",
            flush=True
        )
    except Exception as e:
        print(f"[Simulator Error] Failed to push data: {e}", flush=True)

def push_sensor_data():
    print("=" * 60)
    print("  NIRIKSHAK - Source Firebase RTDB Multi-Sensor Simulator")
    print(f"  Target: {SOURCE_URL}/sensor/history & /sensor/latest")
    print("=" * 60)
    print("Press Ctrl+C to stop.\n")

    cycle = 0
    # Use ThreadPoolExecutor to run requests concurrently in background threads
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    try:
        while True:
            # 1. Generate realistic values for all 5 sensors
            temp_base = 40.0 + (math.sin(cycle * 0.1) * 3.0)
            vib_base  = 1.2 + (math.cos(cycle * 0.05) * 0.3)
            curr_base = 5.2 + (math.sin(cycle * 0.15) * 0.8)
            volt_base = 220.0 + random.uniform(-2, 2)
            rpm_base  = 1250 + int(math.sin(cycle * 0.2) * 40)

            # Inject occasional anomalies for ML testing
            if cycle > 0 and cycle % 15 == 0:
                # Temperature anomaly (>85.0 C)
                temperature = round(random.uniform(88.0, 95.0), 2)
                vibration = round(random.uniform(1.0, 1.8), 3)
                current = round(random.uniform(4.5, 6.0), 2)
                voltage = round(random.uniform(218.0, 222.0), 1)
                rpm = int(random.uniform(1200, 1300))
                print(f"[Simulator] [Anomaly] Overheating Temp={temperature}C")
            elif cycle > 0 and cycle % 15 == 5:
                # Vibration anomaly (>4.0g)
                temperature = round(temp_base, 2)
                vibration = round(random.uniform(4.2, 5.0), 3)
                current = round(random.uniform(4.5, 6.0), 2)
                voltage = round(random.uniform(218.0, 222.0), 1)
                rpm = int(random.uniform(1200, 1300))
                print(f"[Simulator] [Anomaly] Bearing Fault Vib={vibration}g")
            elif cycle > 0 and cycle % 15 == 10:
                # Current anomaly (>10.0A)
                temperature = round(temp_base, 2)
                vibration = round(vib_base, 3)
                current = round(random.uniform(10.5, 12.5), 2)
                voltage = round(random.uniform(218.0, 222.0), 1)
                rpm = int(random.uniform(1200, 1300))
                print(f"[Simulator] [Anomaly] Electrical Fault Curr={current}A")
            else:
                # Normal operational data
                temperature = round(temp_base + random.uniform(-0.5, 0.5), 2)
                vibration = round(vib_base + random.uniform(-0.1, 0.1), 3)
                current = round(curr_base + random.uniform(-0.2, 0.2), 2)
                voltage = round(volt_base, 1)
                rpm = int(rpm_base + random.randint(-10, 10))

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            payload = {
                "temperature": temperature,
                "vibration": vibration,
                "current": current,
                "voltage": voltage,
                "rpm": rpm,
                "timestamp": timestamp
            }

            # Submit the HTTP requests to the executor thread pool (asynchronous)
            executor.submit(send_to_firebase, payload)
            
            cycle += 1
            # Strict 1 second sleep between submissions
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nStopping simulator...")
    finally:
        executor.shutdown(wait=False)

if __name__ == "__main__":
    push_sensor_data()

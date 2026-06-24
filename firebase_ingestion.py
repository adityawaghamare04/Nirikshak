#!/usr/bin/env python3
# ============================================================
#  firebase_ingestion.py — Fetch sensor data from Source Firebase RTDB
#
#  Source: https://dht11-4ed11-default-rtdb.asia-southeast1.firebasedatabase.app/
#  Path:  /sensor/dht11/logs/{push_id} → {temperature, timestamp, ...}
#
#  Replaces the old MQTT-based ingestion (mqtt_subscriber.py)
#  Dynamically adapts to new sensor fields as they are added.
# ============================================================

import os
import sys
import csv
import json
import time
import urllib.request
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config

# ── Shared state (app.py reads this) ─────────────────────
latest_data = {}
last_update_time = 0.0

# ── CSV utilities (carried over from mqtt_subscriber.py) ──
CSV_FIELDS = [
    "timestamp", "temperature", "vibration", "current", "voltage", "rpm", "proximity",
    "temperature_outlier", "vibration_outlier", "current_outlier", "voltage_outlier", "rpm_outlier",
    "operating_hours", "anomaly_status", "anomaly_score", "fault_type", "confidence_score",
    "predicted_rul", "recommended_action", "fault", "probability", "status"
]

RAW_CSV_FIELDS = [
    "timestamp", "temperature", "vibration", "current", "voltage", "rpm", "source_key"
]


def init_csv():
    """Initialize the local machine_data.csv backup (processed ML output)."""
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    csv_path = os.path.join(BASE_DIR, config.DATA_CSV)
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_FIELDS)
        print(f"[CSV] Created {csv_path}", flush=True)


def append_csv(row):
    """Append a processed record to machine_data.csv."""
    csv_path = os.path.join(BASE_DIR, config.DATA_CSV)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writerow(row)


# ── Firebase Source Fetching ─────────────────────────────

def _get_source_url():
    """Get the source Firebase URL from config."""
    return getattr(config, "SOURCE_FIREBASE_URL", "").rstrip("/")


def fetch_all_logs():
    """
    Fetch ALL historical sensor logs from the source Firebase.
    Path: /sensor/history
    Returns a list of dicts sorted by timestamp.
    """
    base = _get_source_url()
    url = f"{base}/sensor/history.json"
    print(f"[Ingestion] Fetching all logs from: {url}", flush=True)

    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())

    if not data or not isinstance(data, dict):
        print("[Ingestion] No data found in source Firebase.", flush=True)
        return []

    rows = []
    for key, val in data.items():
        if isinstance(val, dict):
            val["_key"] = key
            rows.append(val)

    rows.sort(key=lambda x: x.get("timestamp", ""))
    print(f"[Ingestion] Fetched {len(rows)} historical records.", flush=True)
    return rows


def fetch_latest():
    """
    Fetch the latest sensor reading from source Firebase.
    Reads fields under /sensor/latest.
    Returns a dict with available sensor fields, or None.
    """
    base = _get_source_url()
    url = f"{base}/sensor/latest.json"

    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())

    if not data or not isinstance(data, dict):
        return None

    return data


def fetch_new_logs(last_key=None):
    """
    Fetch only new logs added after `last_key` using Firebase REST ordering.
    Returns (list_of_new_rows, new_last_key).
    """
    base = _get_source_url()
    if last_key:
        url = f'{base}/sensor/history.json?orderBy="$key"&startAfter="{last_key}"'
    else:
        url = f"{base}/sensor/history.json"

    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())

    if not data or not isinstance(data, dict):
        return [], last_key

    rows = []
    new_last_key = last_key
    for key, val in sorted(data.items()):
        if isinstance(val, dict):
            val["_key"] = key
            rows.append(val)
            new_last_key = key

    return rows, new_last_key


def save_raw_to_csv(rows, csv_path, append=False):
    """
    Save raw fetched sensor data to an intermediate CSV file.
    This raw CSV is the bridge between ingestion and ML processing.
    """
    dir_name = os.path.dirname(csv_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0
    mode = "a" if append else "w"

    with open(csv_path, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_CSV_FIELDS, extrasaction="ignore")
        if not append or not file_exists:
            writer.writeheader()
        for row in rows:
            csv_row = {
                "timestamp": row.get("timestamp", ""),
                "temperature": row.get("temperature", ""),
                "vibration": row.get("vibration", ""),
                "current": row.get("current", ""),
                "voltage": row.get("voltage", ""),
                "rpm": row.get("rpm", row.get("proximity", "")),
                "source_key": row.get("_key", ""),
            }
            writer.writerow(csv_row)

    print(f"[Ingestion] Saved {len(rows)} rows to {csv_path}", flush=True)


# ── Convenience: one-shot batch ingest ───────────────────

def batch_ingest(csv_path=None):
    """
    One-shot: fetch all logs → save raw CSV → return the CSV path.
    """
    if csv_path is None:
        csv_path = os.path.join(BASE_DIR, "data", "firebase_sensor_data.csv")

    rows = fetch_all_logs()
    if rows:
        save_raw_to_csv(rows, csv_path, append=False)
    return csv_path, rows


# ── Standalone test ──────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Nirikshak — Firebase Source Ingestion Test")
    print("=" * 60)

    # Test: fetch latest
    print("\n[Test] Fetching latest reading...")
    latest = fetch_latest()
    if latest:
        print(f"  Latest: {latest}")
    else:
        print("  No latest data found.")

    # Test: batch ingest
    print("\n[Test] Running batch ingest...")
    path, rows = batch_ingest()
    print(f"  Saved {len(rows)} records to {path}")

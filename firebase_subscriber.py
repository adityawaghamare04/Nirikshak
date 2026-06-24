#!/usr/bin/env python3
# ============================================================
#  firebase_subscriber.py — Real-time Firebase RTDB poller & ML runner
#  Replaces mqtt_subscriber.py for Nirikshak App Ingestion
# ============================================================

import os
import sys
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config
import firebase_ingestion
from ml import model
from pipeline import push_to_firebase

# ── Shared state (app.py reads this) ──────────────────────
latest_data = {}
last_update_time = 0.0

def start():
    """Start the Firebase polling loop in a background thread."""
    global latest_data, last_update_time

    print("[Firebase Subscriber] Starting real-time ingestion loop...", flush=True)
    
    # Initialize/Reset local CSVs
    firebase_ingestion.init_csv()
    raw_csv_path = os.path.join(BASE_DIR, "data", "firebase_sensor_data.csv")

    # Load ML models
    print("[Firebase Subscriber] Loading 3-stage ML models...", flush=True)
    try:
        model.load_models()
        print("[Firebase Subscriber] Models loaded successfully.", flush=True)
    except Exception as e:
        print(f"[Firebase Subscriber] Error loading models: {e}", flush=True)

    # Initialize last key to avoid double-processing historical logs at start
    last_key = None
    try:
        initial_logs = firebase_ingestion.fetch_all_logs()
        if initial_logs:
            last_key = initial_logs[-1]["_key"]
            print(f"[Firebase Subscriber] Initialized starting key to {last_key}", flush=True)
    except Exception as e:
        print(f"[Firebase Subscriber] Error fetching initial logs: {e}", flush=True)

    idx = 0
    while True:
        try:
            # Poll for new logs from Firebase source
            new_rows, new_last_key = firebase_ingestion.fetch_new_logs(last_key)
            
            if new_rows:
                for row in new_rows:
                    # Stage A: Store raw record in intermediate CSV
                    firebase_ingestion.save_raw_to_csv([row], raw_csv_path, append=True)
                    
                    ts_str = row.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    
                    # Stage B: Preprocessing and Cleaning
                    reading = {
                        "timestamp": ts_str,
                        "temperature": float(row['temperature']) if row.get('temperature') is not None else None,
                        "vibration": float(row['vibration']) if row.get('vibration') is not None else None,
                        "current": float(row['current']) if row.get('current') is not None else None,
                        "voltage": float(row['voltage']) if row.get('voltage') is not None else None,
                        "rpm": float(row['rpm']) if row.get('rpm') is not None else None,
                    }
                    
                    # Stage C: Sequential 3-stage ML inference
                    res = model.predict(reading)
                    
                    # Stage D: Output Routing & Delivery
                    record_id = f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx:05d}"
                    
                    raw_data = {
                        "timestamp": ts_str,
                        "temperature": res["temperature"],
                        "vibration": res["vibration"],
                        "current": res["current"],
                        "voltage": res["voltage"],
                        "rpm": res["rpm"]
                    }
                    
                    processed_data = {
                        "timestamp": ts_str,
                        "temperature_scaled": res["temperature"],
                        "vibration_scaled": res["vibration"],
                        "current_scaled": res["current"],
                        "voltage_scaled": res["voltage"],
                        "rpm_scaled": res["rpm"],
                        "temperature_outlier": int(res["temperature_outlier"]),
                        "vibration_outlier": int(res["vibration_outlier"]),
                        "current_outlier": int(res["current_outlier"]),
                        "voltage_outlier": int(res["voltage_outlier"]),
                        "rpm_outlier": int(res["rpm_outlier"]),
                        "operating_hours": res["operating_hours"]
                    }
                    
                    ml_prediction = {
                        "timestamp": ts_str,
                        "anomaly_status": res["anomaly_status"],
                        "anomaly_score": res["anomaly_score"],
                        "fault_type": res["fault_type"],
                        "confidence_score": res["confidence_score"],
                        "predicted_rul": res["predicted_rul"],
                        "recommended_action": res["recommended_action"]
                    }
                    
                    # Push to destination Firebase
                    push_to_firebase(config.FIREBASE_URL, record_id, raw_data, processed_data, ml_prediction, res)
                    
                    # Append to local processed CSV backup
                    res["proximity"] = res["rpm"]
                    firebase_ingestion.append_csv(res)
                    
                    # Update local memory state for app.py
                    latest_data = res
                    last_update_time = time.time()
                    
                    print(
                        f"[Firebase Subscriber] Ingested and processed: Temp={res['temperature']:.1f}C, "
                        f"Status={res['anomaly_status']}, Fault={res['fault_type']} (RUL={res['predicted_rul']:.1f}h)", 
                        flush=True
                    )
                    idx += 1
                
                last_key = new_last_key

        except Exception as e:
            print(f"[Firebase Subscriber] Error in polling loop: {e}", flush=True)
            
        time.sleep(1.0)

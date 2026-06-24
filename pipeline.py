#!/usr/bin/env python3
# ============================================================
#  pipeline.py — Nirikshak IoT Predictive Maintenance Pipeline
#
#  Workflow:
#    Firebase Ingestion → Raw CSV → Preprocessing → 3-Stage ML Inference → Target Firebase
# ============================================================

import os
import sys
import argparse
import time
import json
import urllib.request
import pandas as pd
import numpy as np
from datetime import datetime

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config
import firebase_ingestion
from ml import model

def parse_args():
    parser = argparse.ArgumentParser(description="Nirikshak IoT Processing Pipeline")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["batch", "stream"], 
        default="batch",
        help="Run mode: 'batch' (process all logs from source Firebase) or 'stream' (real-time poll and process)"
    )
    parser.add_argument(
        "--source_url",
        type=str,
        default=config.SOURCE_FIREBASE_URL,
        help="Source Firebase Realtime Database URL (DHT11 logs)"
    )
    parser.add_argument(
        "--firebase_url", 
        type=str, 
        default=config.FIREBASE_URL if (hasattr(config, "FIREBASE_URL") and config.FIREBASE_URL) else "https://nirikshak-project-default-rtdb.firebaseio.com/",
        help="Destination Firebase Realtime Database URL"
    )
    parser.add_argument(
        "--interval", 
        type=float, 
        default=2.0,
        help="Polling interval in seconds (for stream mode)"
    )
    return parser.parse_args()

def push_to_firebase(firebase_url, record_id, raw_data, processed_data, ml_prediction, combined_data):
    """
    Pushes data split across the 3 Firebase collections/paths:
      1. /raw_sensor_data_storage
      2. /processed_data_storage
      3. /ml_prediction_storage
      
    Also updates a unified /sensors/latest and appends to /sensors/history for compatibility.
    """
    headers = {"Content-Type": "application/json"}
    base_url = firebase_url.rstrip('/')
    
    # 1. Push to Raw Sensor Data Storage
    raw_url = f"{base_url}/raw_sensor_data_storage/{record_id}.json"
    req_raw = urllib.request.Request(
        raw_url, data=json.dumps(raw_data).encode(), method="PUT", headers=headers
    )
    
    # 2. Push to Processed Data Storage
    proc_url = f"{base_url}/processed_data_storage/{record_id}.json"
    req_proc = urllib.request.Request(
        proc_url, data=json.dumps(processed_data).encode(), method="PUT", headers=headers
    )
    
    # 3. Push to ML Prediction Storage
    pred_url = f"{base_url}/ml_prediction_storage/{record_id}.json"
    req_pred = urllib.request.Request(
        pred_url, data=json.dumps(ml_prediction).encode(), method="PUT", headers=headers
    )
    
    # 4. Update latest combined record (for dashboard live view)
    latest_url = f"{base_url}/sensors/latest.json"
    req_latest = urllib.request.Request(
        latest_url, data=json.dumps(combined_data).encode(), method="PUT", headers=headers
    )
    
    # 5. Append to history list (for dashboard log compatibility)
    history_url = f"{base_url}/sensors/history.json"
    req_history = urllib.request.Request(
        history_url, data=json.dumps(combined_data).encode(), method="POST", headers=headers
    )
    
    # Execute requests
    try:
        with urllib.request.urlopen(req_raw, timeout=5) as r:
            pass
        with urllib.request.urlopen(req_proc, timeout=5) as r:
            pass
        with urllib.request.urlopen(req_pred, timeout=5) as r:
            pass
        with urllib.request.urlopen(req_latest, timeout=5) as r:
            pass
        with urllib.request.urlopen(req_history, timeout=5) as r:
            pass
        return True
    except Exception as e:
        print(f"  [Firebase Error] Push failed: {e}")
        return False

def run_pipeline():
    args = parse_args()
    
    print("\n" + "=" * 60)
    print("  NIRIKSHAK - FIREBASE TO FIREBASE Predictive Maintenance Pipeline")
    print("=" * 60)
    print(f"Mode:            {args.mode.upper()}")
    print(f"Source Firebase: {args.source_url}")
    print(f"Target Firebase: {args.firebase_url}")
    
    # Ensure models are loaded
    print("[Pipeline] Initializing ML models...")
    model.load_models()
    
    # Initialize/Reset local CSV processed file
    firebase_ingestion.init_csv()

    # 1. Ingestion Phase
    raw_csv_path = os.path.join(BASE_DIR, "data", "firebase_sensor_data.csv")
    
    if args.mode == "batch":
        print("\n[Pipeline] Running BATCH mode. Fetching all historical logs...")
        path, rows = firebase_ingestion.batch_ingest(raw_csv_path)
        if not rows:
            print("[ERROR] No data found in source Firebase logs to ingest.")
            sys.exit(1)
            
        print(f"[Pipeline] Loaded {len(rows)} raw rows from Firebase.")
        
        # Read from raw CSV (Stage B: Preprocessing & Cleaning)
        df = pd.read_csv(raw_csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate operating hours from timestamp deltas
        time_deltas = df['timestamp'].diff().dt.total_seconds() / 3600.0
        time_deltas = time_deltas.fillna(0.0)
        
        cycle_resets = (time_deltas > 2.0).astype(int)
        operating_hours_list = []
        current_acc = 0.0
        for delta, is_reset in zip(time_deltas, cycle_resets):
            if is_reset:
                current_acc = 0.0
            else:
                current_acc += delta
            operating_hours_list.append(current_acc)
        df['operating_hours'] = operating_hours_list
        
        # Stage C & D: ML Inference and Output Routing
        success_count = 0
        limit_rows = min(len(df), 200)  # Limit batch push to avoid rate limits
        print(f"Processing first {limit_rows} rows for ML prediction and Firebase dispatch...")
        
        for idx in range(limit_rows):
            row = df.iloc[idx]
            ts_str = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            
            # Prepare data row with full features (including those missing from DHT11)
            reading = {
                "timestamp": ts_str,
                "temperature": float(row['temperature']) if not pd.isna(row['temperature']) else None,
                "vibration": float(row['vibration']) if not pd.isna(row['vibration']) else None,
                "current": float(row['current']) if not pd.isna(row['current']) else None,
                "voltage": float(row['voltage']) if not pd.isna(row['voltage']) else None,
                "rpm": float(row['rpm']) if not pd.isna(row['rpm']) else None,
                "operating_hours": float(row['operating_hours'])
            }
            
            # Predict
            res = model.predict(reading)
            
            # Construct keys & packages
            record_id = f"rec_{row['timestamp'].strftime('%Y%m%d_%H%M%S')}_{idx:05d}"
            
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
            
            # Route / push
            ok = push_to_firebase(args.firebase_url, record_id, raw_data, processed_data, ml_prediction, res)
            if ok:
                success_count += 1
                
            # Append to local processed CSV
            res["proximity"] = res["rpm"]
            firebase_ingestion.append_csv(res)
            
            if (idx + 1) % 20 == 0 or idx + 1 == limit_rows:
                print(f"  Processed and pushed {idx + 1}/{limit_rows} records...")
                
        print(f"\n[Batch Complete] Successfully processed & pushed {success_count}/{limit_rows} records.")
        
    else: # Stream/Polling mode
        print(f"\n[Pipeline] Running STREAM mode. Polling source Firebase every {args.interval}s...")
        print("Press Ctrl+C to exit.")
        print(f"{'#':>4}  {'Timestamp':<19}  {'Temp':>5}  {'Vib':>6}  {'Curr':>5}  {'Volt':>5}  {'Status':<8}  {'Fault Type':<16}  {'RUL':>5}  Firebase")
        print("-" * 100)
        
        last_key = None
        # Try to find a starting key from current logs to avoid re-processing old entries
        try:
            initial_logs = firebase_ingestion.fetch_all_logs()
            if initial_logs:
                last_key = initial_logs[-1]["_key"]
                print(f"Initialized polling from last key: {last_key}")
        except Exception as e:
            print(f"Could not fetch initial log history (polling all records): {e}")

        idx = 0
        try:
            while True:
                new_rows, new_last_key = firebase_ingestion.fetch_new_logs(last_key)
                if new_rows:
                    for row in new_rows:
                        # Stage A: Save raw to intermediate CSV (Append mode)
                        firebase_ingestion.save_raw_to_csv([row], raw_csv_path, append=True)
                        
                        ts_str = row.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        
                        # Stage B: Preprocessing/Cleaning (model.predict automatically handles missing sensors and scales them)
                        reading = {
                            "timestamp": ts_str,
                            "temperature": float(row['temperature']) if row.get('temperature') is not None else None,
                            "vibration": float(row['vibration']) if row.get('vibration') is not None else None,
                            "current": float(row['current']) if row.get('current') is not None else None,
                            "voltage": float(row['voltage']) if row.get('voltage') is not None else None,
                            "rpm": float(row['rpm']) if row.get('rpm') is not None else None,
                        }
                        
                        # Stage C: Sequential 3-stage inference
                        res = model.predict(reading)
                        
                        # Construct packages
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
                        
                        # Stage D: Output routing
                        ok = push_to_firebase(args.firebase_url, record_id, raw_data, processed_data, ml_prediction, res)
                        status_sym = "[OK]" if ok else "[ERR]"
                        
                        # Save to local processed CSV backup
                        res["proximity"] = res["rpm"]
                        firebase_ingestion.append_csv(res)
                        
                        print(
                            f"{idx+1:>4}  {ts_str}  "
                            f"{res['temperature']:>5.1f}  "
                            f"{res['vibration']:>6.3f}  "
                            f"{res['current']:>5.1f}  "
                            f"{res['voltage']:>5.0f}  "
                            f"{res['anomaly_status']:<8}  "
                            f"{res['fault_type']:<16}  "
                            f"{res['predicted_rul']:>5.1f}  "
                            f"{status_sym}",
                            flush=True
                        )
                        idx += 1
                        
                    last_key = new_last_key
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[Stream Stopped] Exited streaming pipeline.")

if __name__ == "__main__":
    run_pipeline()

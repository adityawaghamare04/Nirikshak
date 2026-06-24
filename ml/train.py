#!/usr/bin/env python3
# ============================================================
#  ml/train.py — Train 3-stage ML Pipeline for Nirikshak
#
#  Models trained:
#    1. Isolation Forest       → Anomaly Detection
#    2. Random Forest Classifier→ Fault Classification
#    3. Random Forest Regressor → RUL Prediction
#
#  Saves:
#    - ml/scaler.pkl
#    - ml/medians.pkl
#    - ml/outlier_bounds.pkl
#    - ml/isolation_forest.pkl
#    - ml/fault_classifier.pkl
#    - ml/rul_regressor.pkl
# ============================================================

import os
import sys
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, accuracy_score, precision_score, 
    recall_score, f1_score, confusion_matrix, mean_squared_error, r2_score
)

# ── Paths ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import config

# Define paths
ML_DIR = os.path.join(BASE_DIR, "ml")
os.makedirs(ML_DIR, exist_ok=True)

TRAINING_CSV = os.path.join(BASE_DIR, "data/nirikshak_historical_data.csv")
SCALER_PATH = os.path.join(ML_DIR, "scaler.pkl")
MEDIANS_PATH = os.path.join(ML_DIR, "medians.pkl")
OUTLIER_BOUNDS_PATH = os.path.join(ML_DIR, "outlier_bounds.pkl")
IF_PATH = os.path.join(ML_DIR, "isolation_forest.pkl")
RFC_PATH = os.path.join(ML_DIR, "fault_classifier.pkl")
RFR_PATH = os.path.join(ML_DIR, "rul_regressor.pkl")
REPORT_PATH = os.path.join(ML_DIR, "evaluation_report.txt")

SENSOR_COLS = ["temperature", "vibration", "current", "voltage", "rpm"]
LABEL_COL = "fault_type"
RUL_COL = "rul"

# ══════════════════════════════════════════════════════════
#  1. GENERATE SYNTHETIC DATA
# ══════════════════════════════════════════════════════════

def generate_nirikshak_dataset(file_path, num_samples=10000):
    """
    Generates a realistic industrial machine degradation dataset.
    Simulates operational runs ending in faults, reset on maintenance.
    """
    print(f"\n[Data Gen] Generating synthetic dataset of {num_samples} rows...")
    np.random.seed(42)
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    records = []
    
    current_time = start_time
    cycle_id = 0
    
    # Fault classes matching the prompt specification
    fault_types = [
        "Bearing Fault", "Misalignment", "Unbalance", 
        "Overheating", "Electrical Fault", "Rotor Fault"
    ]
    
    while len(records) < num_samples:
        cycle_id += 1
        cycle_length_hours = np.random.randint(200, 500) # hours per run
        fault_onset_ratio = np.random.uniform(0.65, 0.85)
        fault_onset_hours = fault_onset_ratio * cycle_length_hours
        
        selected_fault = np.random.choice(fault_types)
        operating_hours = 0.0
        
        while operating_hours < cycle_length_hours and len(records) < num_samples:
            timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Base healthy baseline with standard fluctuations
            volt = np.random.normal(230.0, 0.2)      # V (Centered tightly around 230.0V)
            rpm = volt * 6.3 + np.random.normal(0, 3.0)  # rpm (voltage directly proportional to rpm)
            curr = np.random.normal(5.0, 0.25)       # A
            temp = 25.0 + curr * 8.0 + np.random.normal(0, 1.0) # °C (current directly proportional to heating)
            vib = np.random.normal(0.8, 0.08)        # g
            
            state = "Healthy"
            true_rul = float(cycle_length_hours - operating_hours)
            
            # If we are in the degradation phase, inject progressive fault signature
            if operating_hours >= fault_onset_hours:
                # Severity increases from 0 (onset) to 1 (failure)
                severity = (operating_hours - fault_onset_hours) / (cycle_length_hours - fault_onset_hours)
                state = selected_fault
                
                if selected_fault == "Bearing Fault":
                    # Spikes vibration dramatically, temperature rises moderately
                    vib += np.random.normal(5.0 * severity, 0.3)
                    temp += np.random.normal(15.0 * severity, 0.8)
                elif selected_fault == "Misalignment":
                    # Vibration increases, RPM fluctuates and drops slightly
                    vib += np.random.normal(4.5 * severity, 0.3)
                    rpm -= np.random.normal(100.0 * severity, 10.0)
                elif selected_fault == "Unbalance":
                    # Extremely high vibration only, others relatively stable
                    vib += np.random.normal(6.0 * severity, 0.4)
                elif selected_fault == "Overheating":
                    # Heavy temperature rise, current goes up proportionally
                    curr += np.random.normal(6.5 * severity, 0.3)
                    temp = 25.0 + curr * 8.0 + np.random.normal(0, 1.0)
                elif selected_fault == "Electrical Fault":
                    # Current spikes to high values, voltage drops/fluctuates
                    curr += np.random.normal(8.0 * severity, 0.5)
                    volt -= np.random.normal(15.0 * severity, 2.0)
                    rpm = volt * 6.3 + np.random.normal(0, 3.0)
                    temp = 25.0 + curr * 8.0 + np.random.normal(0, 1.0)
                elif selected_fault == "Rotor Fault":
                    # RPM drops severely, current fluctuates, vibration increases
                    rpm -= np.random.normal(250.0 * severity, 15.0)
                    curr += np.random.normal(2.5 * severity, 0.2)
                    temp = 25.0 + curr * 8.0 + np.random.normal(0, 1.0)
            
            # Occasional random missing data (1%) to test preprocessing
            if np.random.rand() < 0.01:
                # Randomly drop a value
                dropped_sensor = np.random.choice(SENSOR_COLS)
                val_dict = {
                    "timestamp": timestamp_str,
                    "temperature": temp if dropped_sensor != "temperature" else np.nan,
                    "vibration": vib if dropped_sensor != "vibration" else np.nan,
                    "current": curr if dropped_sensor != "current" else np.nan,
                    "voltage": volt if dropped_sensor != "voltage" else np.nan,
                    "rpm": rpm if dropped_sensor != "rpm" else np.nan,
                    "fault_type": state,
                    "rul": true_rul
                }
            else:
                val_dict = {
                    "timestamp": timestamp_str,
                    "temperature": temp,
                    "vibration": vib,
                    "current": curr,
                    "voltage": volt,
                    "rpm": int(rpm) if not np.isnan(rpm) else np.nan,
                    "fault_type": state,
                    "rul": true_rul
                }
                
            records.append(val_dict)
            
            # Step forward in time by 10 minutes
            current_time += timedelta(minutes=10)
            operating_hours += 10.0 / 60.0
            
    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)
    print(f"[Data Gen] Labeled dataset saved successfully to {file_path}")
    print(df["fault_type"].value_counts())


# ══════════════════════════════════════════════════════════
#  2. PIPELINE PREPROCESSING
# ══════════════════════════════════════════════════════════

def preprocess_training_data(df):
    """
    Full pipeline preprocessing steps:
      - Schema validation
      - Handle missing values (median imputation)
      - Outlier handling (flag, don't drop)
      - Feature scaling
      - Compute operating hours from timestamp deltas
    """
    print("\n[Preprocessing] Running preprocessing on raw data...")
    
    # A. Validate Schema
    required_cols = SENSOR_COLS + ["timestamp", LABEL_COL, RUL_COL]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Schema validation failed. Missing columns: {missing_cols}")
        
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # B. Handle Missing Values
    # Impute missing values with column medians, save medians for inference
    medians = {}
    for col in SENSOR_COLS:
        median_val = df[col].median()
        medians[col] = float(median_val)
        df[col] = df[col].fillna(median_val)
        
    # C. Outlier Handling: Flag outliers using absolute user threshold specifications
    outlier_bounds = {
        "temperature": (0.0, 85.0),
        "voltage": (230.0, 230.0),
        "vibration": (0.0, 4.0),
        "current": (0.0, 10.0),
        "rpm": (0.0, 1450.0)
    }
    for col in SENSOR_COLS:
        if col == "temperature":
            df[f"{col}_outlier"] = (df[col] > 85.0).astype(int)
        elif col == "voltage":
            df[f"{col}_outlier"] = (abs(df[col] - 230.0) > 0.5).astype(int)
        elif col == "vibration":
            df[f"{col}_outlier"] = (df[col] > 4.0).astype(int)
        elif col == "current":
            df[f"{col}_outlier"] = (df[col] > 10.0).astype(int)
        elif col == "rpm":
            df[f"{col}_outlier"] = (df[col] > 1450.0).astype(int)
        
    # D. Feature Scaling
    scaler = StandardScaler()
    df[SENSOR_COLS] = scaler.fit_transform(df[SENSOR_COLS])
    
    # E. Compute operating_hours from timestamp deltas
    # (Since this is a simulated set of cycles, deltas are accumulated. Large gaps are capped)
    time_deltas = df['timestamp'].diff().dt.total_seconds() / 3600.0
    time_deltas = time_deltas.fillna(0.0)
    
    # Cap giant gaps (e.g. restarts/maintenance breaks) to reset operating_hours
    # If delta > 2.0 hours, treat it as a cycle reset (new run)
    cycle_resets = (time_deltas > 2.0).astype(int)
    
    # Calculate cumulative operating hours within cycles
    operating_hours = []
    current_acc = 0.0
    for delta, is_reset in zip(time_deltas, cycle_resets):
        if is_reset:
            current_acc = 0.0
        else:
            current_acc += delta
        operating_hours.append(current_acc)
        
    df['operating_hours'] = operating_hours
    
    # Persist the preprocessor models
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(medians, MEDIANS_PATH)
    joblib.dump(outlier_bounds, OUTLIER_BOUNDS_PATH)
    
    print("[Preprocessing] Persistence check:")
    print(f"  StandardScaler saved -> {SCALER_PATH}")
    print(f"  Column Medians saved -> {MEDIANS_PATH}")
    print(f"  Outlier Bounds saved -> {OUTLIER_BOUNDS_PATH}")
    
    return df, scaler, medians, outlier_bounds


# ══════════════════════════════════════════════════════════
#  3. MODEL TRAINING & PIPELINE INTEGRATION
# ══════════════════════════════════════════════════════════

def train_pipeline(df):
    """
    Trains the 3-stage model pipeline:
      Stage 1: Anomaly Detection (Isolation Forest)
      Stage 2: Fault Classification (Random Forest Classifier)
      Stage 3: RUL Prediction (Random Forest Regressor)
    """
    # Features & targets
    X_sensors = df[SENSOR_COLS].values
    y_class = df[LABEL_COL].values
    y_reg = df[RUL_COL].values
    
    # ── Stage 1: Isolation Forest (Unsupervised) ──
    print("\n[Stage 1] Training Isolation Forest for Anomaly Detection...")
    # Train only on Healthy samples to learn normal behavior bounds, or train on all
    # Standard practice: train on all data or mostly normal. Let's use a 5% contamination
    if_model = IsolationForest(contamination=0.08, random_state=42, n_jobs=-1)
    if_model.fit(X_sensors)
    
    # ── Stage 2: Random Forest Classifier (Supervised) ──
    print("[Stage 2] Training Random Forest Classifier for Fault Type...")
    # Train test split for evaluation
    from sklearn.model_selection import train_test_split
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X_sensors, y_class, test_size=0.2, random_state=42, stratify=y_class
    )
    
    rfc_model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rfc_model.fit(X_train_c, y_train_c)
    
    # ── Stage 3: Random Forest Regressor (Supervised) ──
    print("[Stage 3] Training Random Forest Regressor for RUL Prediction...")
    # Inputs: 5 sensors + operating_hours
    X_reg_inputs = np.column_stack((X_sensors, df['operating_hours'].values))
    
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X_reg_inputs, y_reg, test_size=0.2, random_state=42
    )
    
    rfr_model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rfr_model.fit(X_train_r, y_train_r)
    
    # Persist the models
    joblib.dump(if_model, IF_PATH)
    joblib.dump(rfc_model, RFC_PATH)
    joblib.dump(rfr_model, RFR_PATH)
    
    print("\n[Model Persistence] All 3 models saved successfully:")
    print(f"  Isolation Forest   -> {IF_PATH}")
    print(f"  Random Forest Clf  -> {RFC_PATH}")
    print(f"  Random Forest Reg  -> {RFR_PATH}")
    
    return {
        "if_model": if_model,
        "rfc_model": rfc_model,
        "rfr_model": rfr_model,
        "clf_data": (X_test_c, y_test_c),
        "reg_data": (X_test_r, y_test_r),
        "all_data": (X_sensors, y_class, y_reg)
    }


# ══════════════════════════════════════════════════════════
#  4. EVALUATION & REPORTING
# ══════════════════════════════════════════════════════════

def evaluate_models(models_dict, df):
    """
    Evaluates each stage of the pipeline and saves/prints the metrics report.
    """
    print("\n[Evaluation] Evaluating pipeline stages...")
    if_model = models_dict["if_model"]
    rfc_model = models_dict["rfc_model"]
    rfr_model = models_dict["rfr_model"]
    
    X_test_c, y_test_c = models_dict["clf_data"]
    X_test_r, y_test_r = models_dict["reg_data"]
    X_sensors, y_class, y_reg = models_dict["all_data"]
    
    # 1. Evaluate Anomaly Detector (Isolation Forest)
    # Map model outputs: -1 = Anomaly, 1 = Normal
    if_preds = if_model.predict(X_sensors)
    anomaly_status = np.where(if_preds == -1, "Anomaly", "Normal")
    anomaly_scores = -if_model.score_samples(X_sensors) # higher score = more anomalous
    
    # Map true faults vs healthy for binary comparison
    true_anomalies = np.where(y_class != "Healthy", "Anomaly", "Normal")
    
    if_acc = accuracy_score(true_anomalies, anomaly_status)
    if_f1 = f1_score(true_anomalies, anomaly_status, pos_label="Anomaly")
    
    # 2. Evaluate Fault Classifier
    y_pred_c = rfc_model.predict(X_test_c)
    acc_c = accuracy_score(y_test_c, y_pred_c)
    f1_c = f1_score(y_test_c, y_pred_c, average="weighted")
    cm_c = confusion_matrix(y_test_c, y_pred_c)
    classes = rfc_model.classes_
    
    # 3. Evaluate RUL Regressor
    y_pred_r = rfr_model.predict(X_test_r)
    mse_r = mean_squared_error(y_test_r, y_pred_r)
    rmse_r = np.sqrt(mse_r)
    mae_r = np.mean(np.abs(y_test_r - y_pred_r))
    r2_r = r2_score(y_test_r, y_pred_r)
    
    # Create printed/saved report
    report_content = []
    report_content.append("=" * 60)
    report_content.append("  NIRIKSHAK ML PIPELINE EVALUATION REPORT")
    report_content.append("=" * 60)
    report_content.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    report_content.append("STAGE 1: ANOMALY DETECTION (Isolation Forest)")
    report_content.append("-" * 45)
    report_content.append(f"Accuracy vs Labeled Faults: {if_acc * 100:.2f}%")
    report_content.append(f"F1-Score (Anomaly class):   {if_f1:.4f}")
    report_content.append(f"Anomaly Score Bounds:        Min={anomaly_scores.min():.4f}, Max={anomaly_scores.max():.4f}")
    report_content.append(f"Anomaly Threshold (default): 0.50 (where score_samples < -0.5)\n")
    
    report_content.append("STAGE 2: FAULT CLASSIFICATION (Random Forest Classifier)")
    report_content.append("-" * 45)
    report_content.append(f"Test Set Accuracy:   {acc_c * 100:.2f}%")
    report_content.append(f"Weighted F1 Score:   {f1_c:.4f}\n")
    report_content.append("Classification Report:")
    report_content.append(classification_report(y_test_c, y_pred_c))
    
    report_content.append("Confusion Matrix:")
    # Format matrix nicely
    header_str = f"{'':20}" + "".join([f"{cls[:10]:>12}" for cls in classes])
    report_content.append(header_str)
    for idx, row in enumerate(cm_c):
        row_str = f"{classes[idx][:20]:<20}" + "".join([f"{val:>12}" for val in row])
        report_content.append(row_str)
    report_content.append("\n")
    
    report_content.append("STAGE 3: REMAINING USEFUL LIFE (Random Forest Regressor)")
    report_content.append("-" * 45)
    report_content.append(f"Root Mean Squared Error (RMSE): {rmse_r:.2f} hours")
    report_content.append(f"Mean Absolute Error (MAE):      {mae_r:.2f} hours")
    report_content.append(f"R-squared (R2) Score:           {r2_r:.4f}")
    report_content.append("=" * 60)
    
    report_txt = "\n".join(report_content)
    print(report_txt)
    
    with open(REPORT_PATH, "w") as f:
        f.write(report_txt)
    print(f"\n[Evaluation] Report saved successfully to {REPORT_PATH}")


# ══════════════════════════════════════════════════════════
#  MAIN RUNNER
# ══════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 60)
    print("  Nirikshak — Pipeline Model Training Module")
    print("=" * 60)
    
    # 1. Dataset availability check
    if not os.path.exists(TRAINING_CSV):
        print(f"Training dataset not found at {TRAINING_CSV}.")
        generate_nirikshak_dataset(TRAINING_CSV, num_samples=10000)
    else:
        print(f"Found existing training dataset at {TRAINING_CSV}")
        
    df_raw = pd.read_csv(TRAINING_CSV)
    
    # 2. Run Preprocessing Pipeline
    df_prep, scaler, medians, outlier_bounds = preprocess_training_data(df_raw)
    
    # 3. Train Models
    models_dict = train_pipeline(df_prep)
    
    # 4. Evaluate Models & Output Report
    evaluate_models(models_dict, df_prep)
    
    print("\n" + "=" * 60)
    print("  [SUCCESS] 3-STAGE ML MODEL TRAINING PIPELINE COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
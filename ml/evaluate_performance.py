#!/usr/bin/env python3
# ============================================================
#  ml/evaluate_performance.py — Performance Evaluation Script
# ============================================================

import os
import sys
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, accuracy_score, precision_score, 
    recall_score, f1_score, confusion_matrix, mean_squared_error, r2_score
)

# ── Paths ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

ML_DIR = os.path.join(BASE_DIR, "ml")
TRAINING_CSV = os.path.join(BASE_DIR, "data/nirikshak_historical_data.csv")

SCALER_PATH = os.path.join(ML_DIR, "scaler.pkl")
IF_PATH = os.path.join(ML_DIR, "isolation_forest.pkl")
RFC_PATH = os.path.join(ML_DIR, "fault_classifier.pkl")
RFR_PATH = os.path.join(ML_DIR, "rul_regressor.pkl")
OUTPUT_IMG = os.path.join(ML_DIR, "evaluation_plots.png")

SENSOR_COLS = ["temperature", "vibration", "current", "voltage", "rpm"]
LABEL_COL = "fault_type"
RUL_COL = "rul"

def load_data_and_preprocess():
    print(f"[1/4] Loading training dataset from {TRAINING_CSV}...")
    if not os.path.exists(TRAINING_CSV):
        raise FileNotFoundError(f"Historical dataset not found at {TRAINING_CSV}. Please run train.py first to generate it.")
        
    df = pd.read_csv(TRAINING_CSV)
    
    # Load scaling preprocessors
    print("Loading scaler.pkl...")
    scaler = joblib.load(SCALER_PATH)
    
    # Preprocess
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Impute missing values
    for col in SENSOR_COLS:
        df[col] = df[col].fillna(df[col].median())
        
    # Standard scale
    df[SENSOR_COLS] = scaler.transform(df[SENSOR_COLS])
    
    # Re-calculate operating hours
    time_deltas = df['timestamp'].diff().dt.total_seconds() / 3600.0
    time_deltas = time_deltas.fillna(0.0)
    cycle_resets = (time_deltas > 2.0).astype(int)
    
    operating_hours = []
    current_acc = 0.0
    for delta, is_reset in zip(time_deltas, cycle_resets):
        if is_reset:
            current_acc = 0.0
        else:
            current_acc += delta
        operating_hours.append(current_acc)
        
    df['operating_hours'] = operating_hours
    return df

def evaluate():
    df = load_data_and_preprocess()
    
    print("\n[2/4] Loading trained models...")
    if_model = joblib.load(IF_PATH)
    rfc_model = joblib.load(RFC_PATH)
    rfr_model = joblib.load(RFR_PATH)
    
    # Features & Targets
    X_sensors = df[SENSOR_COLS].values
    y_class = df[LABEL_COL].values
    y_reg = df[RUL_COL].values
    
    # Train-test split (matching train.py random state 42)
    # Stage 2: Classifier split
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X_sensors, y_class, test_size=0.2, random_state=42, stratify=y_class
    )
    # Stage 3: Regressor split (Sensor features + operating_hours)
    X_reg_inputs = np.column_stack((X_sensors, df['operating_hours'].values))
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X_reg_inputs, y_reg, test_size=0.2, random_state=42
    )
    
    # -------------------------------------------------------------
    # 1. Evaluate Anomaly Detection (Isolation Forest)
    # -------------------------------------------------------------
    print("\n[3/4] Running Anomaly Detection Evaluation...")
    if_preds = if_model.predict(X_sensors)
    # Isolation Forest outputs: -1 (anomaly), 1 (normal)
    pred_anomalies = np.where(if_preds == -1, "Anomaly", "Normal")
    true_anomalies = np.where(y_class != "Healthy", "Anomaly", "Normal")
    
    if_acc = accuracy_score(true_anomalies, pred_anomalies)
    if_prec = precision_score(true_anomalies, pred_anomalies, pos_label="Anomaly")
    if_rec = recall_score(true_anomalies, pred_anomalies, pos_label="Anomaly")
    if_f1 = f1_score(true_anomalies, pred_anomalies, pos_label="Anomaly")
    
    # -------------------------------------------------------------
    # 2. Evaluate Fault Classification (Random Forest Classifier)
    # -------------------------------------------------------------
    print("Running Fault Classification Evaluation...")
    y_pred_c = rfc_model.predict(X_test_c)
    clf_report = classification_report(y_test_c, y_pred_c, output_dict=True)
    clf_accuracy = accuracy_score(y_test_c, y_pred_c)
    conf_mat = confusion_matrix(y_test_c, y_pred_c)
    classes = rfc_model.classes_
    
    # -------------------------------------------------------------
    # 3. Evaluate Lifespan Estimation (Random Forest Regressor)
    # -------------------------------------------------------------
    print("Running Lifespan (RUL) Prediction Evaluation...")
    y_pred_r = rfr_model.predict(X_test_r)
    mse = mean_squared_error(y_test_r, y_pred_r)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test_r, y_pred_r)
    
    # -------------------------------------------------------------
    # Print Performance Metrics to Terminal
    # -------------------------------------------------------------
    print("\n" + "="*70)
    print("                 NIRIKSHAK PIPELINE PARAMETER EVALUATION")
    print("="*70)
    
    print("\n>>> OVERALL SYSTEM PERFORMANCE:")
    print(f"  Anomaly Detector Accuracy:  {if_acc*100:.2f}%")
    print(f"  Fault Classifier Accuracy:  {clf_accuracy*100:.2f}%")
    print(f"  RUL Regressor R² Score:     {r2:.4f} (RMSE: {rmse:.2f} Hours)")
    
    print("\n>>> STAGE 1: ANOMALY DETECTION (Isolation Forest)")
    print(f"  Precision: {if_prec:.4f}")
    print(f"  Recall:    {if_rec:.4f}")
    print(f"  F1-Score:  {if_f1:.4f}")
    
    print("\n>>> STAGE 2: FAULT CLASSIFICATION METRIC MATRIX:")
    print(f"  {'Class':<22} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("  " + "-" * 60)
    for c in classes:
        metrics = clf_report[c]
        print(f"  {c:<22} | {metrics['precision']:<10.4f} | {metrics['recall']:<10.4f} | {metrics['f1-score']:<10.4f}")
    
    print("\n>>> STAGE 2: CONFUSION MATRIX:")
    # Custom print
    title_label = 'Actual \\ Pred'
    header = f"  {title_label:<22} | " + " | ".join([f"{c[:10]:^10}" for c in classes])
    print(header)
    print("  " + "-" * len(header))
    for idx, row in enumerate(conf_mat):
        row_str = f"  {classes[idx]:<22} | " + " | ".join([f"{val:^10}" for val in row])
        print(row_str)
        
    print("\n>>> STAGE 3: LIFESPAN REGRESSION METRICS:")
    print(f"  Root Mean Squared Error (RMSE): {rmse:.4f} Hours")
    print(f"  R-Squared (R²):                 {r2:.4f}")
    print("="*70)
    
    # -------------------------------------------------------------
    # 4. Generate Visual Plots
    # -------------------------------------------------------------
    print(f"\n[4/4] Generating evaluation plots image -> {OUTPUT_IMG}...")
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.patch.set_facecolor('#0f0f16')
    
    # A. Confusion Matrix Plot
    ax_cm = axes[0]
    ax_cm.set_facecolor('#0f0f16')
    im = ax_cm.imshow(conf_mat, interpolation='nearest', cmap=plt.cm.Oranges)
    ax_cm.set_title("Fault Classifier Confusion Matrix", color='#f1f0ee', fontsize=14, pad=15)
    fig.colorbar(im, ax=ax_cm, fraction=0.046, pad=0.04)
    
    tick_marks = np.arange(len(classes))
    ax_cm.set_xticks(tick_marks)
    ax_cm.set_xticklabels([c[:12] for c in classes], rotation=45, ha='right', color='#f1f0ee')
    ax_cm.set_yticks(tick_marks)
    ax_cm.set_yticklabels(classes, color='#f1f0ee')
    
    # Annotate values inside matrix
    thresh = conf_mat.max() / 2.
    for i in range(conf_mat.shape[0]):
        for j in range(conf_mat.shape[1]):
            ax_cm.text(j, i, format(conf_mat[i, j], 'd'),
                     ha="center", va="center",
                     color="white" if conf_mat[i, j] > thresh else "black")
            
    ax_cm.set_ylabel('True Fault Type', color='#f1f0ee', fontsize=12, labelpad=10)
    ax_cm.set_xlabel('Predicted Fault Type', color='#f1f0ee', fontsize=12, labelpad=10)
    ax_cm.spines['bottom'].set_color('#333333')
    ax_cm.spines['left'].set_color('#333333')
    ax_cm.spines['top'].set_visible(False)
    ax_cm.spines['right'].set_visible(False)
    
    # B. Actual vs Predicted RUL Plot
    ax_rul = axes[1]
    ax_rul.set_facecolor('#0f0f16')
    ax_rul.scatter(y_test_r, y_pred_r, alpha=0.3, color='#ffa94d', edgecolors='none', label='Data points')
    
    # Perfect fit line
    ideal_line_val = [y_test_r.min(), y_test_r.max()]
    ax_rul.plot(ideal_line_val, ideal_line_val, 'r--', lw=2.5, color='#ff6b6b', label='Ideal prediction')
    
    ax_rul.set_title("Remaining Useful Life (RUL): Actual vs Predicted", color='#f1f0ee', fontsize=14, pad=15)
    ax_rul.set_xlabel("Actual RUL (Hours)", color='#f1f0ee', fontsize=12, labelpad=10)
    ax_rul.set_ylabel("Predicted RUL (Hours)", color='#f1f0ee', fontsize=12, labelpad=10)
    ax_rul.tick_params(colors='#f1f0ee')
    ax_rul.grid(True, color='#222228', linestyle='--', alpha=0.5)
    ax_rul.legend(facecolor='#0f0f16', edgecolor='#222228', labelcolor='#f1f0ee')
    
    ax_rul.spines['bottom'].set_color('#333333')
    ax_rul.spines['left'].set_color('#333333')
    ax_rul.spines['top'].set_visible(False)
    ax_rul.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMG, dpi=180, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    
    print("[SUCCESS] Evaluation plots saved!")

if __name__ == "__main__":
    evaluate()

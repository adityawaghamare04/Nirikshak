# Nirikshak - IoT-Based Predictive Maintenance Platform

Nirikshak is an advanced, production-grade Industrial Internet of Things (IIoT) predictive maintenance system designed to monitor, clean, analyze, and forecast the health of rotating machinery (e.g. industrial motor drives). 

The platform continuously streams physical parameters (Temperature, Vibration, Current, Voltage, RPM) from edge devices via secure MQTT, processes them through a sequential **3-Stage Machine Learning Inference Pipeline**, logs results locally, syncs them to the cloud (Firebase Realtime Database), and presents real-time visualizations on a high-fidelity, responsive **glassmorphic dashboard**.

---

## 🌟 Core Features

- 📡 **Real-Time Data Ingestion & Sync**: Listens to MQTT/Firebase RTDB data streams at low latency (2-second interval cycles), parsing JSON payloads.
- 🧠 **3-Stage Sequential ML Inference**: 
  - **Stage 1: Anomaly Detection** (Isolation Forest) flags unexpected operations.
  - **Stage 2: Fault Classification** (Random Forest Classifier) determines exact fault categories with confidence percentages.
  - **Stage 3: RUL Estimation** (Random Forest Regressor) estimates the machine's remaining useful life in hours.
- ⚙️ **Robust Preprocessing & Feature Engineering**: Handles missing values via precalculated medians, flags outlier values using absolute physical boundaries without dropping records, and scales variables using a fitted `StandardScaler`.
- 🛡️ **Fault-Tolerant Rule-Based Fallback**: Dynamically drops back to deterministic rule-based inferences if model pickle files are missing or corrupted, ensuring 100% platform availability.
- 📊 **Premium Glassmorphic Dashboard**: Translucent cards, custom radial glows, and time-series charts (powered by Flask-SocketIO and Chart.js).
- 🔍 **Interactive Diagnostic Modals**: Clicking any parameter card displays a modal detailing historical sparklines (last 50 values), window statistics (min, max, average), and physical limits.
- 🔄 **Ingestion Watchdog Simulator**: Automatically detects idle telemetry states (no updates for > 5 seconds) and injects simulated data to keep dashboard sessions active and testable.

---

## 🛠️ Technology Stack

- **Backend Web Server**: Python 3.10+, Flask 3.0.x with Eventlet (asynchronous concurrency loop).
- **Real-Time Messaging**: Flask-SocketIO (WebSockets), Paho-MQTT (HiveMQ Cloud secure TLS broker).
- **Cloud Database**: Firebase Realtime Database (via HTTPS REST / Python SDK).
- **Machine Learning Core**: Scikit-Learn (v1.4.2), Joblib (model serialization), NumPy, Pandas.
- **Frontend Core**: HTML5, Vanilla CSS (Glassmorphism layout tokens), JavaScript (Socket.IO client, Chart.js v4.4).

---

## 📁 Repository Directory Structure

```text
nirikshak/
├── app.py                      # Flask web server, SocketIO hub, and watchdog simulator
├── config.py                   # Central configurations, physical thresholds, and env loaders
├── firebase_subscriber.py      # Background poller thread that runs the ML pipeline & database sync
├── firebase_simulator.py       # Simulated telemetry streamer pushing live logs to Firebase
├── firebase_ingestion.py       # Helper functions to query, filter, and write raw logs to database
├── firebase_rules.json         # Security rules configuration for Firebase Realtime Database
├── pipeline.py                 # Core routing script to sync telemetry records to Firebase nodes
├── generate_report.py          # PDF document compiler using fpdf2
├── requirements.txt            # Project python dependencies
├── Nirikshak_System_Report.pdf # Compiled PDF technical report
├── .env                        # Local environment variables (Firebase URLs, ports)
│
├── ml/                         # Machine Learning Modules
│   ├── model.py                # Pipeline preprocessing, lazy-loaders, and unified predict() entry
│   ├── train.py                # Model training, feature engineering, and pickle serialization script
│   ├── evaluate_performance.py # Model evaluation, confusion matrix generation, and plotting script
│   ├── evaluation_report.txt   # Model metrics printout (accuracy, precision, recall, confusion matrix)
│   ├── evaluation_plots.png    # Plotted ROC, confusion matrix, and feature importance charts
│   ├── scaler.pkl              # Saved StandardScaler preprocessor
│   ├── medians.pkl             # Precalculated sensor median values for imputation
│   ├── outlier_bounds.pkl      # Saved mathematical outlier threshold criteria
│   ├── isolation_forest.pkl    # Stage 1: Unsupervised Anomaly Detection model
│   ├── fault_classifier.pkl    # Stage 2: Fault Type Classification model
│   └── rul_regressor.pkl       # Stage 3: RUL Regression model
│
├── utils/                      # Helper Utilities
│   └── data_cleaner.py         # IQR outlier cleaning, single-record range check, and rolling features
│
├── templates/                  # Frontend HTML templates
│   ├── index.html              # Marketing/Introductory platform landing page
│   └── dashboard.html          # Dynamic glassmorphic administration console
│
├── static/                     # Image assets & logs
│   ├── logoo.png               # Project branding logo
│   └── motor_png_1.png         # 3D motor graphic asset
│
└── data/                       # Local data stores (Git ignored)
    ├── firebase_sensor_data.csv# Local backup log containing raw ingested sensor payloads
    └── pdm_motor_dataset_100k.csv  # 100K training source dataset
```

---

## 🧠 3-Stage Sequential ML Pipeline

Nirikshak separates predictive maintenance calculations into three specific stages to maximize stability and speed:

```
[Raw Telemetry] ➔ [Imputation & Range Flags] ➔ [StandardScaler]
                                                       │
                                                       ▼
                                            [Stage 1: Isolation Forest]
                                            (Classifies Normal vs Anomaly)
                                                       │
                                                       ▼
                                       [Stage 2: Random Forest Classifier]
                                       (Identifies Bearing, Rotor, etc.)
                                                       │
                                                       ▼
                                       [Stage 3: Random Forest Regressor]
                                       (Estimates RUL hours using speed/load)
```

### Model Performance Metrics

Our models are trained and validated using `ml/evaluate_performance.py`, generating the following results (`ml/evaluation_report.txt`):

- **Stage 1 (Anomaly Detection - Isolation Forest)**:
  - **Accuracy vs Labeled Faults**: **86.58%**
  - **Anomaly Score Bounds**: Min = 0.3291, Max = 0.7817
- **Stage 2 (Fault Classification - Random Forest Classifier)**:
  - **Overall Accuracy**: **97.95%**
  - **F1-Scores by Class**:
    - Bearing Fault: `0.92` (F1)
    - Electrical Fault: `0.94` (F1)
    - Healthy State: `0.99` (F1)
    - Misalignment: `0.94` (F1)
    - Overheating: `0.74` (F1)
    - Rotor Fault: `0.97` (F1)
    - Unbalance: `0.94` (F1)

---

## 🚀 Setup & Execution Guide

### 1. Installation

Clone the repository and enter the directory:
```bash
git clone https://github.com/adityawaghamare04/Nirikshak.git
cd Nirikshak
```

Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

Install python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Database & Environment Configuration

Create a `.env` file in the project root:
```env
# Flask Settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# Firebase Realtime Database
FIREBASE_URL=https://nirikshak-project-default-rtdb.firebaseio.com/
SOURCE_FIREBASE_URL=https://dht11-4ed11-default-rtdb.asia-southeast1.firebasedatabase.app/
```

### 3. Training & Evaluation (Optional)

If you need to retrain the pipeline models using `pdm_motor_dataset_100k.csv`:
```bash
python ml/train.py
```
To evaluate the models and generate plots:
```bash
python ml/evaluate_performance.py
```

### 4. Running the Platform

To run the complete platform, start the components in separate shells:

1. **Start the Web Dashboard**:
   ```bash
   python app.py
   ```
   *Dashboard will be available at: [http://localhost:5000](http://localhost:5000)*

2. **Start the Real-time Ingestion & ML Loop**:
   ```bash
   python firebase_subscriber.py
   ```

3. **Start the Live Simulator (For Testing)**:
   If you don't have active physical edge hardware connected, run the simulator to stream mock telemetry logs:
   ```bash
   python firebase_simulator.py
   ```

---

## 📄 Documentation

For a comprehensive review of the codebase design, data schema specifications, mathematical preprocessing definitions, and visual design parameters, see the generated technical specification report:
📄 **[Nirikshak_System_Report.pdf](./Nirikshak_System_Report.pdf)**

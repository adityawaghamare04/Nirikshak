import os
import sys
from fpdf import FPDF
from datetime import datetime

class NirikshakReportPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return # Skip header on cover page
        
        # Primary Color Theme
        self.set_text_color(26, 54, 93) # Deep Blue (#1A365D)
        self.set_font("helvetica", "B", 8)
        self.cell(0, 10, "NIRIKSHAK - IoT-BASED PREDICTIVE MAINTENANCE PLATFORM", border="B", ln=1, align="L")
        self.ln(5)

    def footer(self):
        if self.page_no() == 1:
            return # Skip footer on cover page
            
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(113, 128, 150) # Gray (#718096)
        
        # Print page number right-aligned
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="R")
        self.set_x(20)
        self.cell(0, 10, "Nirikshak Technical Specification Report - Confidential", align="L")

    def chapter_title(self, label):
        self.set_font("helvetica", "B", 14)
        self.set_text_color(26, 54, 93) # Deep Blue
        # Draw background bar for section titles
        self.set_fill_color(235, 248, 250) # Light Ice Blue
        self.cell(0, 10, f"  {label}", ln=True, fill=True)
        self.ln(4)

    def section_subtitle(self, label):
        self.set_font("helvetica", "B", 11)
        self.set_text_color(43, 108, 176) # Teal/Blue (#2B6CB0)
        self.cell(0, 8, label, ln=True)
        self.ln(2)

    def body_text(self, text, style="", size=10):
        self.set_font("helvetica", style, size)
        self.set_text_color(45, 55, 72) # Slate (#2D3748)
        self.multi_cell(0, 6, text)
        self.ln(3)

    def bullet_point(self, label, text):
        self.set_font("helvetica", "B", 10)
        self.set_text_color(26, 54, 93)
        self.write(6, f"- {label}: ")
        self.set_font("helvetica", "", 10)
        self.set_text_color(45, 55, 72)
        self.write(6, f"{text}\n")
        self.ln(1)

def build_pdf(filename="Nirikshak_System_Report.pdf"):
    pdf = NirikshakReportPDF()
    pdf.alias_nb_pages()
    pdf.set_margins(20, 20, 20)
    
    # ================= PAGE 1: COVER PAGE =================
    pdf.add_page()
    
    # Decorative elements
    pdf.set_fill_color(26, 54, 93) # Deep Blue
    pdf.rect(0, 0, 15, 297, "F") # Left blue stripe
    
    pdf.set_fill_color(43, 108, 176) # Light Blue
    pdf.rect(15, 0, 5, 297, "F") # Left accent stripe
    
    # Top spacing
    pdf.ln(40)
    
    # Title
    pdf.set_font("helvetica", "B", 32)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(10) # Left margin offset
    pdf.multi_cell(0, 12, "NIRIKSHAK")
    
    # Subtitle
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(43, 108, 176)
    pdf.cell(10)
    pdf.multi_cell(0, 8, "IoT-Based Predictive Maintenance Platform")
    
    pdf.ln(10)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(74, 85, 104)
    pdf.cell(10)
    pdf.multi_cell(0, 6, "A Comprehensive Report on Architecture, Preprocessing Pipelines,\nMachine Learning Specifications, and Code Implementation.")
    
    # Separation line
    pdf.ln(20)
    pdf.cell(10)
    pdf.set_draw_color(43, 108, 176)
    pdf.set_line_width(1)
    pdf.line(30, pdf.get_y(), 190, pdf.get_y())
    
    # Metadata footer
    pdf.ln(60)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(26, 54, 93)
    
    metadata = [
        ("PROJECT TYPE", "IIoT Predictive Maintenance"),
        ("DATE GENERATED", datetime.now().strftime("%B %d, %Y")),
        ("BACKEND ENGINE", "Flask & Socket.IO (Eventlet)"),
        ("MACHINE LEARNING", "3-Stage Sequential Inference Pipeline"),
        ("DOCUMENT VERSION", "1.0.0 (Production-Ready)")
    ]
    
    for label, val in metadata:
        pdf.cell(10)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(113, 128, 150)
        pdf.cell(45, 6, f"{label}:")
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(45, 55, 72)
        pdf.cell(0, 6, val, ln=True)
    
    # ================= PAGE 2: PROJECT OVERVIEW & TECH STACK =================
    pdf.add_page()
    pdf.chapter_title("1. System Overview & Technology Stack")
    
    pdf.body_text(
        "Nirikshak is an advanced Industrial Internet of Things (IIoT) predictive maintenance platform designed "
        "to continuously monitor the mechanical and electrical health of industrial motor drives. It ingests high-frequency "
        "telemetry variables, performs automated signal preprocessing, runs a multi-stage sequential Machine Learning "
        "inference pipeline, and projects real-time analytics to a high-fidelity glassmorphic web dashboard."
    )
    
    pdf.section_subtitle("Core Technology Stack")
    pdf.body_text(
        "The system architecture is engineered using reliable open-source frameworks and libraries "
        "capable of high-throughput real-time telemetry processing:"
    )
    
    tech_stack = [
        ("Operating System", "Platform Agnostic (Windows / Linux / macOS) for flexible local or cloud deployments."),
        ("Backend Framework", "Python 3.10+ with Flask 3.0.x and Eventlet to enable high-concurrency event loops."),
        ("Real-time Gateway", "Flask-SocketIO establishing low-latency WebSocket connections for immediate data push."),
        ("ML Core Libraries", "Scikit-Learn (v1.4.2) for classical machine learning models and Joblib for serialization."),
        ("Data Handling", "Pandas and NumPy for vectorization, feature scaling, and statistics calculations."),
        ("Message Broker", "MQTT (HiveMQ Cloud broker using secure TLS/SSL encryption) for standard telemetry ingestion."),
        ("Database Storage", "Firebase Realtime Database (HTTPS REST / SDK) for real-time cloud data synchronization."),
        ("Frontend Client", "HTML5, Vanilla CSS (Glassmorphism layout tokens), Chart.js (v4.4), and Socket.IO client-side JS.")
    ]
    for label, text in tech_stack:
        pdf.bullet_point(label, text)
        
    pdf.ln(5)
    pdf.section_subtitle("Monitored Sensor Parameters")
    pdf.body_text(
        "The system reads five physical variables from the edge sensors (e.g. ESP32 + DHT11 + ADXL345 + ACS712) "
        "to construct the motor drive state footprint:"
    )
    sensors = [
        ("Temperature (C)", "Monitors operational heat. Spikes indicate bearing friction or electrical overload."),
        ("Vibration (g)", "Captures acceleration forces. Excessive vibration points to mechanical misalignment or bearing faults."),
        ("Current (A)", "Measures electrical current draw. Overcurrent flags winding short circuits or heavy physical load."),
        ("Voltage (V)", "Tracks terminal voltage supply. Fluctuations can trigger electrical instability warnings."),
        ("RPM / Speed", "Indicates rotor rotation rate. Slip fluctuations or low speeds point to load mismatch or broken rotor bars.")
    ]
    for label, text in sensors:
        pdf.bullet_point(label, text)

    # ================= PAGE 3: SYSTEM ARCHITECTURE & PIPELINE =================
    pdf.add_page()
    pdf.chapter_title("2. System Architecture & Ingestion Pipeline")
    
    pdf.body_text(
        "Nirikshak employs a decoupled, event-driven system architecture designed to isolate ingestion bottlenecks "
        "from telemetry processing and frontend rendering. The pipeline comprises four structural blocks:"
    )
    
    pdf.section_subtitle("A. Telemetry Ingestion (Sensor to Broker)")
    pdf.body_text(
        "Physical edge sensors (DHT11, ADXL345, ACS712) linked to an ESP32 microcontroller publish JSON-formatted "
        "readings to HiveMQ Cloud. For staging or testing environments, a CSV Data Simulator (e.g. firebase_simulator.py) "
        "streams historical logs at regular 2-second intervals, simulating live operations."
    )
    
    pdf.section_subtitle("B. Ingestion Loop (firebase_subscriber.py)")
    pdf.body_text(
        "A dedicated background polling thread continuously checks the Firebase RTDB source node. When a new log "
        "is detected, the subscriber intercepts the raw dictionary, saves a backup copy to a local CSV repository "
        "(data/firebase_sensor_data.csv) to guarantee offline audit logs, and routes the dict directly to the ML engine."
    )
    
    pdf.section_subtitle("C. Inference & Routing (pipeline.py & ml/model.py)")
    pdf.body_text(
        "The telemetry is passed through the 3-stage sequential ML models. The resulting enriched prediction payload "
        "is instantly routed in two directions: (1) it is written to the primary visualization database in Firebase "
        "under structured nodes, and (2) it updates the local state in app.py, triggering a WebSocket broadcast."
    )

    pdf.section_subtitle("D. Client-Side Rendering (app.py to Browser)")
    pdf.body_text(
        "Flask-SocketIO broadcasts the prediction payload ('sensor_update' event) to all connected dashboard "
        "sessions. The client UI intercepts this WebSocket message and updates the gauges, status indicators, and "
        "time-series charts dynamically within a 2-second cycle."
    )
    
    # Ingestion Pipeline Diagram text description
    pdf.ln(5)
    pdf.set_fill_color(248, 249, 250)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(pdf.get_x(), pdf.get_y(), 170, 32, "FD")
    
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 6, "  Data Pipeline Architecture Map:", ln=True)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(74, 85, 104)
    pdf.cell(0, 5, "    [Sensors/Simulator] -> [HiveMQ Cloud MQTT / Firebase] -> [firebase_subscriber.py]", ln=True)
    pdf.cell(0, 5, "                                                                        | (Inference)", ln=True)
    pdf.cell(0, 5, "    [dashboard.html Webpage] <- [Socket.IO Broadcast] <- [app.py Server] <- [ml/model.py Engine]", ln=True)

    # ================= PAGE 4: PREPROCESSING & FEATURE ENGINEERING =================
    pdf.add_page()
    pdf.chapter_title("3. Data Preprocessing & Feature Engineering")
    
    pdf.body_text(
        "To ensure high stability and model inference accuracy, raw data inputs from physical sensors "
        "must be cleaned, imputed, and scaled before entering the machine learning models. The system runs "
        "the following pipeline defined in ml/model.py:"
    )
    
    pdf.section_subtitle("1. Parameter Alias Resolution")
    pdf.body_text(
        "Different ingestion scripts may output slightly different naming conventions. The preprocessor resolves "
        "common aliases (e.g. mapping 'temp', 'Temperature(C)', and 'Temperature' to 'temperature') to normalize "
        "keys before subsequent data steps."
    )
    
    pdf.section_subtitle("2. Missing Value Imputation (medians.pkl)")
    pdf.body_text(
        "If a sensor fails or registers null values, the preprocessor loads a precalculated medians dictionary "
        "('medians.pkl') compiled from the training dataset. This replaces the null with a typical healthy parameter, "
        "preventing runtime exceptions in the model pipeline."
    )
    
    pdf.section_subtitle("3. Outlier Flagging (Flag-Not-Drop)")
    pdf.body_text(
        "Rather than dropping records containing anomalies, the system flags outliers based on absolute thresholds. "
        "This allows the models to run on all rows while keeping the dashboard updated on limit violations:"
    )
    
    bounds = [
        ("Temperature Outlier", "Flagged if temperature exceeds 85.0 C."),
        ("Vibration Outlier", "Flagged if RMS vibration acceleration exceeds 4.0 g."),
        ("Current Outlier", "Flagged if current consumption exceeds 10.0 A."),
        ("Voltage Outlier", "Flagged if supply voltage deviates from the nominal 230.0 V by more than 0.5 V."),
        ("RPM Outlier", "Flagged if motor rotation speed exceeds 1450.0 RPM.")
    ]
    for label, text in bounds:
        pdf.bullet_point(label, text)
        
    pdf.ln(3)
    pdf.section_subtitle("4. Standardization (scaler.pkl)")
    pdf.body_text(
        "A pre-trained StandardScaler scales the imputed sensor values into a normal distribution with "
        "mean=0 and variance=1. This ensures that features with larger physical units (like RPM at 1450) do not "
        "dominate features with smaller physical units (like vibration at 0.8) during model calculations."
    )

    pdf.section_subtitle("5. Rolling Features (utils/data_cleaner.py)")
    pdf.body_text(
        "For historical batch analyses, the system uses a 5-step rolling window to generate the rolling mean "
        "and rolling standard deviation for temperature, vibration, and current. This captures time-series trend "
        "dynamics, enabling the models to recognize progressive failures."
    )

    # ================= PAGE 5: 3-STAGE MACHINE LEARNING ENGINE =================
    pdf.add_page()
    pdf.chapter_title("4. The 3-Stage Machine Learning Engine")
    
    pdf.body_text(
        "Nirikshak implements a sequential three-stage Machine Learning engine. Each model is chosen for its "
        "specific ability to address anomaly detection, categorical classification, or regression prediction:"
    )
    
    # Table Header
    pdf.set_fill_color(26, 54, 93)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 10, " Inference Stage", border=1, fill=True)
    pdf.cell(40, 10, " Model Selection", border=1, fill=True)
    pdf.cell(30, 10, " Primary Outputs", border=1, fill=True)
    pdf.cell(65, 10, " Design Rationale & Benefits", border=1, fill=True, ln=True)
    
    # Table Content rows
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(45, 55, 72)
    
    # Row 1
    x, y = pdf.get_x(), pdf.get_y()
    pdf.rect(x, y, 35, 24)
    pdf.multi_cell(35, 6, "\nStage 1:\nAnomaly Detection")
    pdf.set_xy(x + 35, y)
    pdf.rect(x + 35, y, 40, 24)
    pdf.multi_cell(40, 6, "\nIsolation Forest\n(isolation_forest.pkl)")
    pdf.set_xy(x + 75, y)
    pdf.rect(x + 75, y, 30, 24)
    pdf.multi_cell(30, 6, "Anomaly Status\n(Normal/Anomaly)\nAnomaly Score")
    pdf.set_xy(x + 105, y)
    pdf.rect(x + 105, y, 65, 24)
    pdf.multi_cell(65, 4, "Unsupervised algorithm that isolates anomalies in high-dimensional feature spaces by partitioning data. Highly efficient for flagging unexpected deviations from nominal footprints without requiring balanced labels.")
    pdf.set_xy(x, y + 24)
    
    # Row 2
    x, y = pdf.get_x(), pdf.get_y()
    pdf.rect(x, y, 35, 24)
    pdf.multi_cell(35, 6, "\nStage 2:\nFault Classification")
    pdf.set_xy(x + 35, y)
    pdf.rect(x + 35, y, 40, 24)
    pdf.multi_cell(40, 6, "\nRandom Forest\nClassifier\n(fault_classifier.pkl)")
    pdf.set_xy(x + 75, y)
    pdf.rect(x + 75, y, 30, 24)
    pdf.multi_cell(30, 6, "Fault Class\n(e.g., Bearing, Rotor)\nConfidence %")
    pdf.set_xy(x + 105, y)
    pdf.rect(x + 105, y, 65, 24)
    pdf.multi_cell(65, 4, "Ensemble classifier combining decision trees to capture non-linear relationships. Predicts exact failure category and provides probability scores to prevent false alarms.")
    pdf.set_xy(x, y + 24)

    # Row 3
    x, y = pdf.get_x(), pdf.get_y()
    pdf.rect(x, y, 35, 22)
    pdf.multi_cell(35, 5, "\nStage 3:\nRUL Estimation")
    pdf.set_xy(x + 35, y)
    pdf.rect(x + 35, y, 40, 22)
    pdf.multi_cell(40, 5, "\nRandom Forest\nRegressor\n(rul_regressor.pkl)")
    pdf.set_xy(x + 75, y)
    pdf.rect(x + 75, y, 30, 22)
    pdf.multi_cell(30, 5, "\nRemaining Useful\nLife (RUL) in Hours")
    pdf.set_xy(x + 105, y)
    pdf.rect(x + 105, y, 65, 22)
    pdf.multi_cell(65, 4, "Combines normalized sensor variables and cumulative operating hours to project the remaining lifespan before breakdown. Crucial for scheduling preventive maintenance windows.")
    pdf.set_xy(x, y + 22)

    pdf.ln(5)
    pdf.section_subtitle("Robust Rule-Based Fallback System")
    pdf.body_text(
        "To guarantee high system availability and fault tolerance, ml/model.py includes an embedded fallback logic "
        "(_rule_based_fallback). If the model pickle files are missing, deleted, or corrupted, the system catches the "
        "exception and falls back to a deterministic rule-based framework. This maps sensor anomalies (e.g. temperature > 75C, "
        "vibration > 4.5g) to predefined fault categories and estimates RUL using linear wear functions. The resulting payload "
        "features a 'model_source: rule-based-fallback' tag, keeping the UI dashboard running."
    )

    # ================= PAGE 6: CODEBASE IMPLEMENTATION DETAILS =================
    pdf.add_page()
    pdf.chapter_title("5. Codebase Structure & Core Modules")
    
    pdf.body_text(
        "The Nirikshak codebase is organized into modular components. Below is the file structure and explanation "
        "of the core python scripts:"
    )
    
    modules = [
        ("config.py", "Central configuration module that loads environment variables from a local .env file. It contains definitions for Flask port numbers, database URLs, and the physical sensor thresholds (TEMP_MAX, CURRENT_MAX, etc.)."),
        ("ml/model.py", "The core ML execution engine. It lazy-loads all model files (scaler.pkl, isolation_forest.pkl, etc.) on demand. Includes the pre-processing logic, cumulative operating hours calculation (using datetime deltas), rule-based fallbacks, and the unified predict() entry point."),
        ("firebase_subscriber.py", "A real-time database listener running in a background thread. It polls the Firebase RTDB ingest node, extracts incoming sensor parameters, executes the ML models, appends backups locally, and pushes predictions to the destination DB node."),
        ("utils/data_cleaner.py", "A collection of data cleansing helper routines. Handles single-record range check validations and batch CSV operations such as Interquartile Range (IQR) outlier removal and rolling statistical feature calculations."),
        ("app.py", "The Flask web server hosting application endpoints. It launches the background thread tasks, acts as the SocketIO websocket hub, serves static web pages, and implements a watchdog timer that injects simulated telemetry if live ingestion pauses for over 5 seconds."),
        ("templates/dashboard.html", "The frontend dashboard utilizing a dark, modern glassmorphic interface. It binds to the websocket client, displaying live parameters across customizable dial gauges, rendering historical time-series charts, and hosting interactive diagnostic modals.")
    ]
    
    for mod_name, description in modules:
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(43, 108, 176)
        pdf.cell(0, 6, f" {mod_name}", ln=True)
        pdf.set_font("helvetica", "", 9.5)
        pdf.set_text_color(45, 55, 72)
        pdf.multi_cell(0, 5, description)
        pdf.ln(2)

    pdf.section_subtitle("Visual Design and UI Glassmorphism")
    pdf.body_text(
        "The frontend design uses high-contrast translucent cards, backdrop-filter blurs, and radial gradients. "
        "It features color-coded status elements: Green for Healthy operation (Normal), Yellow for warning levels, and "
        "Red for critical Anomaly status, giving operators instant machine status updates."
    )

    # ================= PAGE 7: WORKFLOW SUMMARY & DIAGNOSTIC MODALS =================
    pdf.add_page()
    pdf.chapter_title("6. Execution Workflow & Operation")
    
    pdf.body_text(
        "The operational lifecycle of a telemetry data point from the machine to the cloud and dashboard follows "
        "a structured pipeline. The sequence is detailed below:"
    )
    
    workflow_steps = [
        ("Step 1: Edge Acquisition", "Edge sensors publish temperature, vibration, voltage, current, and RPM variables to the broker every 2 seconds."),
        ("Step 2: Database Ingestion", "The subscriber polls the source Firebase node and extracts the new reading payload."),
        ("Step 3: Feature Engineering", "The raw payload is imputed using 'medians.pkl', checked for outliers, and standardized using the scaler."),
        ("Step 4: Model Inference", "The scaled array passes through Stage 1 (Isolates anomalies), Stage 2 (Classifies fault type), and Stage 3 (Estimates RUL)."),
        ("Step 5: Logging and Sync", "The output is appended to 'data/firebase_sensor_data.csv' and synchronized to the Firebase destination DB nodes."),
        ("Step 6: Dashboard Update", "Socket.IO emits the prediction data, and the web browser updates the interactive UI gauges and time-series charts instantly.")
    ]
    for step, desc in workflow_steps:
        pdf.bullet_point(step, desc)

    pdf.ln(4)
    pdf.section_subtitle("Interactive Diagnostic Modal System")
    pdf.body_text(
        "To allow operators to perform deep diagnostics on individual sensors, the dashboard features a custom "
        "modal overlay. When clicking any sensor card, a detailed overlay displays: (1) historical sparklines plotting the "
        "last 50 parameters, (2) computed statistics (minimum, maximum, average) over the window, and (3) absolute physical limits. "
        "This aids in preventive maintenance decision-making."
    )
    
    pdf.ln(5)
    pdf.section_subtitle("Maintenance Action Recommendations")
    pdf.body_text(
        "The system generates recommended diagnostic actions based on the classified fault type:\n"
        " - Healthy: 'Continue normal operations. Next check in 250 operating hours.'\n"
        " - Bearing Fault: 'Inspect bearing housing for wear or lack of lubrication. Schedule check within 24 hrs.'\n"
        " - Misalignment: 'Re-align shaft coupling. Schedule check within 48 hrs.'\n"
        " - Overheating: 'Check cooling fans and motor ventilation immediately. Reduce operating load.'\n"
        " - Electrical Fault: 'Inspect stator winding, terminal voltage, and cables. Risk of short circuit!'\n"
        " - Critical (<24 hrs RUL): 'CRITICAL ALERT: Machine failure imminent! Shut down and inspect immediately!'"
    )
    
    # Save PDF
    pdf.output(filename)
    print(f"[PDF Generator] Successfully compiled PDF to: {filename}")

if __name__ == "__main__":
    build_pdf()

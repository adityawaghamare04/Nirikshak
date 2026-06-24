import os

# ============================================================
#  config.py — Nirikshak Project Configuration
# ============================================================

def _load_env_file(filepath=".env"):
    """Loads key-value pairs from a local .env file into os.environ."""
    # Try looking in project root
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, filepath)
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        os.environ[key] = val
        except Exception as e:
            print(f"[Config Loader] Warning: Could not read .env file: {e}")

# Load local environment variables if .env exists
_load_env_file()

# --- HiveMQ Cloud (Free Tier) ---
MQTT_BROKER    = os.environ.get("MQTT_BROKER", "27ba182fd536475e8a5d3195430f436b.s1.eu.hivemq.cloud")
MQTT_PORT      = int(os.environ.get("MQTT_PORT", "8883"))
MQTT_USERNAME  = os.environ.get("MQTT_USERNAME", "Shriraj2004")
MQTT_PASSWORD  = os.environ.get("MQTT_PASSWORD", "Shriraj2004")
MQTT_TOPIC     = os.environ.get("MQTT_TOPIC", "nirikshak/machine1")
MQTT_CLIENT_ID = os.environ.get("MQTT_CLIENT_ID", "nirikshak_subscriber")

# --- Data ---
DATA_CSV      = "data/machine_data.csv"
TRAINING_CSV  = "data/training_data.csv"
MODEL_PATH    = "ml/rf_model.pkl"

# --- Flask ---
FLASK_HOST    = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT    = int(os.environ.get("FLASK_PORT", "5000"))
FLASK_DEBUG   = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")

# --- ML Thresholds (all 5 sensors) ---
TEMP_MAX        = float(os.environ.get("TEMP_MAX", "85.0"))      # °C
CURRENT_MAX     = float(os.environ.get("CURRENT_MAX", "10.0"))    # A
VOLTAGE_NOMINAL = float(os.environ.get("VOLTAGE_NOMINAL", "230.0"))  # V
VIBRATION_MAX   = float(os.environ.get("VIBRATION_MAX", "4.0"))      # g
PROXIMITY_MAX   = int(os.environ.get("PROXIMITY_MAX", "1450"))       # rpm

# --- Firebase Realtime Database URL ---
FIREBASE_URL  = os.environ.get("FIREBASE_URL", "https://nirikshak-project-default-rtdb.firebaseio.com/")

# --- Firebase Source Ingestion Database URL ---
SOURCE_FIREBASE_URL = os.environ.get("SOURCE_FIREBASE_URL", "https://dht11-4ed11-default-rtdb.asia-southeast1.firebasedatabase.app/")

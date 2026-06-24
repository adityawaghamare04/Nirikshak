#!/usr/bin/env python3
# ============================================================
#  utils/alerts.py — Nirikshak Alert and Notification Utility
#  Supports Twilio SMS notifications with built-in rate-limiting/cooldown
# ============================================================

import os
import sys
import time
import base64
import urllib.request
import urllib.parse
import json

# Add parent path to allow configuration import
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config

# Module-level state to manage SMS rate limiting/cooldown
last_sms_sent_time = 0.0

def send_twilio_sms(body):
    """
    Sends an SMS message using Twilio's REST API.
    Uses Python's built-in urllib to avoid external dependencies (e.g. twilio SDK).
    """
    sid = getattr(config, "TWILIO_ACCOUNT_SID", "")
    token = getattr(config, "TWILIO_AUTH_TOKEN", "")
    from_num = getattr(config, "TWILIO_FROM_NUMBER", "")
    to_num = getattr(config, "TWILIO_TO_NUMBER", "")

    # Basic validations
    if not sid or "YOUR_TWILIO" in sid:
        print("[Alert System] SMS skipped: Twilio ACCOUNT_SID is not configured in config.py.", flush=True)
        return False
    if not token or "YOUR_TWILIO" in token:
        print("[Alert System] SMS skipped: Twilio AUTH_TOKEN is not configured in config.py.", flush=True)
        return False
    if not from_num or "XX" in from_num:
        print("[Alert System] SMS skipped: Twilio FROM_NUMBER is not configured in config.py.", flush=True)
        return False
    if not to_num or "XX" in to_num:
        print("[Alert System] SMS skipped: Twilio TO_NUMBER is not configured in config.py.", flush=True)
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    
    # URL encode parameters
    data_dict = {
        "To": to_num,
        "From": from_num,
        "Body": body
    }
    data = urllib.parse.urlencode(data_dict).encode("utf-8")
    
    # Basic Authorization Header
    auth_str = f"{sid}:{token}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_content = json.loads(response.read().decode())
            print(f"[Alert System] SMS alert sent successfully! Message SID: {res_content.get('sid')}", flush=True)
            return True
    except urllib.error.HTTPError as he:
        try:
            err_body = he.read().decode()
            print(f"[Alert System] Failed to send SMS via Twilio API (HTTP {he.code}): {err_body}", flush=True)
        except Exception:
            print(f"[Alert System] Failed to send SMS via Twilio API: {he}", flush=True)
        return False
    except Exception as e:
        print(f"[Alert System] Failed to send SMS via Twilio API: {e}", flush=True)
        return False

def trigger_anomaly_alert(prediction):
    """
    Decides whether to send an SMS alert based on the prediction status
    and checks the alert cooldown (rate limiting).
    """
    global last_sms_sent_time
    
    anomaly_status = prediction.get("anomaly_status", "Normal")
    fault_type = prediction.get("fault_type", "Healthy")
    
    if anomaly_status != "Anomaly":
        return
        
    now = time.time()
    cooldown = getattr(config, "SMS_ALERT_COOLDOWN", 300)
    
    # Check rate limit/cooldown
    if now - last_sms_sent_time < cooldown:
        remaining = int(cooldown - (now - last_sms_sent_time))
        # Log to console that an alert was throttled
        print(f"[Alert System] Anomaly detected but SMS throttled (cooldown active: {remaining}s remaining).", flush=True)
        return

    # Construct the alert message body
    timestamp = prediction.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
    temp = prediction.get("temperature", 0.0)
    vib = prediction.get("vibration", 0.0)
    curr = prediction.get("current", 0.0)
    volt = prediction.get("voltage", 0.0)
    rpm = prediction.get("rpm", 0)
    rul = prediction.get("predicted_rul", 0.0)
    action = prediction.get("recommended_action", "Check machine immediately.")

    body = (
        f"⚠️ NIRIKSHAK ALERT ⚠️\n"
        f"Anomaly detected at {timestamp}!\n"
        f"Fault Type: {fault_type}\n"
        f"Sensors:\n"
        f" - Temp: {temp:.1f} C\n"
        f" - Vib: {vib:.3f} g\n"
        f" - Curr: {curr:.2f} A\n"
        f" - Volt: {volt:.1f} V\n"
        f" - Speed: {rpm} RPM\n"
        f"Est. RUL: {rul:.1f} hours\n"
        f"Rec. Action: {action}"
    )
    
    print(f"[Alert System] Triggering alert for fault: {fault_type}...", flush=True)
    success = send_twilio_sms(body)
    if success:
        last_sms_sent_time = now

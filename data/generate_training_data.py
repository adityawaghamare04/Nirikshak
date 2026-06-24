import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)
n = 1000
start = datetime.now() - timedelta(hours=n // 30)
timestamps = [start + timedelta(minutes=2 * i) for i in range(n)]

# Normal readings (first 80%)
temp      = np.random.normal(45, 5, n)
vibration = np.random.normal(0.8, 0.2, n)
current   = np.random.normal(5.0, 0.5, n)
humidity  = np.random.normal(55, 8, n)
label     = np.zeros(n, dtype=int)

# Inject faults into last 20%
fault_start = int(n * 0.80)
num_faults  = n - fault_start

temp[fault_start:]      = np.random.normal(78, 6, num_faults)
vibration[fault_start:] = np.random.normal(3.2, 0.5, num_faults)
current[fault_start:]   = np.random.normal(10.5, 1.0, num_faults)
label[fault_start:]     = 1

df = pd.DataFrame({
    "timestamp":   timestamps,
    "temperature": np.clip(temp, 20, 130).round(2),
    "vibration":   np.clip(vibration, 0, 10).round(3),
    "current":     np.clip(current, 0, 20).round(2),
    "humidity":    np.clip(humidity, 20, 95).round(1),
    "fault":       label
})

os.makedirs("data", exist_ok=True)
df.to_csv("data/training_data.csv", index=False)

normal_count = (label == 0).sum()
fault_count  = (label == 1).sum()
print(f"Generated {n} samples")
print(f"  Normal : {normal_count} ({normal_count/n*100:.0f}%)")
print(f"  Fault  : {fault_count}  ({fault_count/n*100:.0f}%)")
print(f"Saved to data/training_data.csv")
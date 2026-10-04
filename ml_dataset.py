import pandas as pd
import random

data = []

for _ in range(2000):

    heart_rate = random.randint(55, 140)
    movement = random.uniform(0, 10)
    battery = random.randint(1, 100)
    signal_strength = random.randint(0, 100)
    time_since_heartbeat = random.randint(1, 120)
    location_change = random.uniform(0, 5)
    check_in_overdue = random.randint(0, 1)

    # Risk calculation used to create training labels
    risk = 0

    if heart_rate > 110 or heart_rate < 50:
        risk += 20

    if movement < 2:
        risk += 15

    if battery < 15:
        risk += 20

    if signal_strength < 30:
        risk += 15

    if time_since_heartbeat > 30:
        risk += 20

    if location_change == 0:
        risk += 5

    if check_in_overdue == 1:
        risk += 20

    # Safety class
    if risk <= 25:
        safety_status = "Safe"

    elif risk <= 50:
        safety_status = "Caution"

    elif risk <= 75:
        safety_status = "High Risk"

    else:
        safety_status = "Emergency"

    data.append([
        heart_rate,
        movement,
        battery,
        signal_strength,
        time_since_heartbeat,
        location_change,
        check_in_overdue,
        safety_status
    ])


columns = [
    "heart_rate",
    "movement",
    "battery",
    "signal_strength",
    "time_since_heartbeat",
    "location_change",
    "check_in_overdue",
    "safety_status"
]

df = pd.DataFrame(data, columns=columns)

df.to_csv(
    "safety_dataset.csv",
    index=False
)

print("✅ Dataset created successfully!")
print(f"Total records: {len(df)}")
print("\nSafety distribution:")
print(df["safety_status"].value_counts())
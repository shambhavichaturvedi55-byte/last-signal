import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# ---------------- LOAD DATASET ----------------

df = pd.read_csv("safety_dataset.csv")

# ---------------- FEATURES ----------------

X = df[
    [
        "heart_rate",
        "movement",
        "battery",
        "signal_strength",
        "time_since_heartbeat",
        "location_change",
        "check_in_overdue"
    ]
]

# Target
y = df["safety_status"]

# ---------------- TRAIN / TEST SPLIT ----------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training records:", len(X_train))
print("Testing records:", len(X_test))

# ---------------- RANDOM FOREST ----------------

model = RandomForestClassifier(
    n_estimators=150,
    random_state=42,
    class_weight="balanced"
)

model.fit(X_train, y_train)

# ---------------- PREDICTION ----------------

y_pred = model.predict(X_test)

# ---------------- ACCURACY ----------------

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n==============================")
print("🤖 LAST SIGNAL ML MODEL")
print("==============================")

print(
    f"\nModel Accuracy: "
    f"{accuracy * 100:.2f}%"
)

# ---------------- CLASSIFICATION REPORT ----------------

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred
    )
)

# ---------------- CONFUSION MATRIX ----------------

print("Confusion Matrix:")
print(
    confusion_matrix(
        y_test,
        y_pred
    )
)

# ---------------- FEATURE IMPORTANCE ----------------

print("\nFeature Importance:")

importance = pd.DataFrame({
    "Feature": X.columns,
    "Importance": model.feature_importances_
})

importance = importance.sort_values(
    by="Importance",
    ascending=False
)

print(importance)

# ---------------- SAVE MODEL ----------------

import joblib

joblib.dump(
    model,
    "last_signal_model.pkl"
)

print(
    "\n✅ ML model saved as "
    "last_signal_model.pkl"
)
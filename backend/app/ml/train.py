import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_COLUMNS = [
    "fan_in", "fan_out", "total_in_usd", "total_out_usd", "pass_through_ratio",
    "round_amount_ratio", "age_days", "burstiness", "mixer_exposure", "bridge_exposure", "dormant_flag"
]

def generate_synthetic_training_data(n_samples: int = 2500):
    np.random.seed(42)
    data = []
    labels = []

    # Roles: normal, victim, collector, intermediary, peel, vasp_deposit, mixer
    role_names = ["normal", "victim", "collector", "intermediary", "peel", "vasp_deposit", "mixer"]

    for _ in range(n_samples):
        role = np.random.choice(role_names, p=[0.25, 0.15, 0.15, 0.15, 0.10, 0.10, 0.10])
        labels.append(role)

        if role == "normal":
            fan_in = np.random.randint(1, 6)
            fan_out = np.random.randint(1, 6)
            total_in = np.random.uniform(50, 3000)
            total_out = total_in * np.random.uniform(0.1, 0.9)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.05, 0.35)
            age_days = np.random.uniform(30, 800)
            burstiness = np.random.uniform(0.1, 2.0)
            mixer_exp = 1.0 if np.random.rand() < 0.02 else 0.0
            bridge_exp = 1.0 if np.random.rand() < 0.03 else 0.0
            dormant = 0.0

        elif role == "victim":
            fan_in = np.random.randint(1, 4)
            fan_out = np.random.randint(1, 3)
            total_in = np.random.uniform(500, 20000)
            total_out = total_in * np.random.uniform(0.90, 0.99)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.3, 0.8)
            age_days = np.random.uniform(5, 300)
            burstiness = np.random.uniform(0.5, 3.0)
            mixer_exp = 0.0
            bridge_exp = 0.0
            dormant = 0.0

        elif role == "collector":
            fan_in = np.random.randint(6, 35)
            fan_out = np.random.randint(1, 5)
            total_in = np.random.uniform(15000, 250000)
            total_out = total_in * np.random.uniform(0.85, 1.0)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.15, 0.6)
            age_days = np.random.uniform(5, 90)
            burstiness = np.random.uniform(4.0, 22.0)
            mixer_exp = 1.0 if np.random.rand() < 0.05 else 0.0
            bridge_exp = 1.0 if np.random.rand() < 0.25 else 0.0
            dormant = 0.0

        elif role == "intermediary":
            fan_in = np.random.randint(2, 8)
            fan_out = np.random.randint(2, 10)
            total_in = np.random.uniform(8000, 120000)
            total_out = total_in * np.random.uniform(0.92, 1.0)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.1, 0.45)
            age_days = np.random.uniform(2, 60)
            burstiness = np.random.uniform(3.0, 18.0)
            mixer_exp = 1.0 if np.random.rand() < 0.05 else 0.0
            bridge_exp = 1.0 if np.random.rand() < 0.45 else 0.0
            dormant = 0.0

        elif role == "peel":
            fan_in = np.random.randint(1, 3)
            fan_out = np.random.randint(2, 4)
            total_in = np.random.uniform(12000, 90000)
            total_out = total_in * np.random.uniform(0.95, 1.0)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.08, 0.35)
            age_days = np.random.uniform(1, 30)
            burstiness = np.random.uniform(1.5, 10.0)
            mixer_exp = 0.0
            bridge_exp = 0.0
            dormant = 0.0

        elif role == "vasp_deposit":
            fan_in = np.random.randint(12, 70)
            fan_out = np.random.randint(1, 3)
            total_in = np.random.uniform(40000, 600000)
            total_out = total_in * np.random.uniform(0.98, 1.0)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.05, 0.35)
            age_days = np.random.uniform(20, 500)
            burstiness = np.random.uniform(6.0, 35.0)
            mixer_exp = 0.0
            bridge_exp = 1.0 if np.random.rand() < 0.15 else 0.0
            dormant = 0.0

        else:  # mixer
            fan_in = np.random.randint(25, 250)
            fan_out = np.random.randint(25, 250)
            total_in = np.random.uniform(80000, 2500000)
            total_out = total_in * np.random.uniform(0.95, 1.0)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.75, 1.0)
            age_days = np.random.uniform(45, 1000)
            burstiness = np.random.uniform(8.0, 60.0)
            mixer_exp = 1.0
            bridge_exp = 1.0 if np.random.rand() < 0.55 else 0.0
            dormant = 0.0

        data.append([
            float(fan_in), float(fan_out), float(total_in), float(total_out),
            float(pass_through), float(round_ratio), float(age_days),
            float(burstiness), float(mixer_exp), float(bridge_exp), float(dormant)
        ])

    return pd.DataFrame(data, columns=FEATURE_COLUMNS), pd.Series(labels)

def train_and_save_models():
    print("Training ChainNetra forensic ML models...")
    X, y = generate_synthetic_training_data(2500)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    # 1. Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X_train, y_train)

    train_preds = rf.predict(X_train)
    test_preds = rf.predict(X_test)
    train_acc = accuracy_score(y_train, train_preds)
    test_acc = accuracy_score(y_test, test_preds)
    cm = confusion_matrix(y_test, test_preds).tolist()
    classes = rf.classes_.tolist()

    rf_path = os.path.join(MODEL_DIR, "wallet_role_rf.joblib")
    joblib.dump(rf, rf_path)

    # 2. Isolation Forest Anomaly Detector
    iso = IsolationForest(contamination=0.12, random_state=42)
    iso.fit(X_train)
    iso_path = os.path.join(MODEL_DIR, "anomaly_iso.joblib")
    joblib.dump(iso, iso_path)

    # 3. Model Card Metrics with explicit caveat and feature order
    metrics = {
        "model_name": "ChainNetra Wallet Role & Anomaly Classifier",
        "training_data_type": "Deterministic Synthetic Multi-Chain Forensic Patterns",
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "train_accuracy": round(float(train_acc), 4),
        "held_out_test_accuracy": round(float(test_acc), 4),
        "accuracy": round(float(test_acc), 4),
        "classes": classes,
        "feature_order": FEATURE_COLUMNS,
        "feature_count": len(FEATURE_COLUMNS),
        "confusion_matrix": cm,
        "feature_importances": dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in rf.feature_importances_])),
        "caveat": "Trained on deterministic synthetic forensic patterns. Accuracy does NOT reflect real-world adversarial evasion or unobserved novel obfuscation patterns. Intended solely for investigative triage support.",
        "trained_at": datetime.now(timezone.utc).isoformat()
    }
    metrics_path = os.path.join(MODEL_DIR, "model_card.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Models successfully trained! Held-out test accuracy: {test_acc*100:.2f}%. Saved to {MODEL_DIR}")
    return metrics

if __name__ == "__main__":
    train_and_save_models()

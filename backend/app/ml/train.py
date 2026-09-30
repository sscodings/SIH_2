import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def generate_synthetic_training_data(n_samples: int = 1500):
    np.random.seed(42)
    data = []
    labels = []

    # Roles: 0: normal, 1: victim, 2: collector, 3: intermediary, 4: peel, 5: vasp_deposit, 6: mixer
    role_names = ["normal", "victim", "collector", "intermediary", "peel", "vasp_deposit", "mixer"]

    for _ in range(n_samples):
        role = np.random.choice(role_names, p=[0.25, 0.15, 0.15, 0.15, 0.10, 0.10, 0.10])
        labels.append(role)

        if role == "normal":
            fan_in = np.random.randint(1, 4)
            fan_out = np.random.randint(1, 4)
            total_in = np.random.uniform(50, 2000)
            total_out = total_in * np.random.uniform(0.1, 0.9)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.05, 0.3)
            age_days = np.random.uniform(30, 800)
            burstiness = np.random.uniform(0.1, 1.5)
            mixer_exp = 0.0
            bridge_exp = 0.0
            dormant = 0.0

        elif role == "victim":
            fan_in = np.random.randint(1, 3)
            fan_out = 1
            total_in = np.random.uniform(500, 15000)
            total_out = total_in * 0.98
            pass_through = 0.98
            round_ratio = np.random.uniform(0.4, 0.8)
            age_days = np.random.uniform(10, 300)
            burstiness = np.random.uniform(0.5, 2.0)
            mixer_exp = 0.0
            bridge_exp = 0.0
            dormant = 0.0

        elif role == "collector":
            fan_in = np.random.randint(8, 30)
            fan_out = np.random.randint(1, 4)
            total_in = np.random.uniform(20000, 250000)
            total_out = total_in * np.random.uniform(0.9, 1.0)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.2, 0.6)
            age_days = np.random.uniform(5, 60)
            burstiness = np.random.uniform(5.0, 20.0)
            mixer_exp = 0.0
            bridge_exp = 0.2
            dormant = 0.0

        elif role == "intermediary":
            fan_in = np.random.randint(2, 6)
            fan_out = np.random.randint(2, 8)
            total_in = np.random.uniform(10000, 100000)
            total_out = total_in * np.random.uniform(0.95, 1.0)
            pass_through = total_out / total_in
            round_ratio = np.random.uniform(0.1, 0.4)
            age_days = np.random.uniform(2, 40)
            burstiness = np.random.uniform(4.0, 15.0)
            mixer_exp = 0.0
            bridge_exp = 0.4
            dormant = 0.0

        elif role == "peel":
            fan_in = 1
            fan_out = 2
            total_in = np.random.uniform(15000, 80000)
            total_out = total_in * 0.99
            pass_through = 0.99
            round_ratio = np.random.uniform(0.1, 0.3)
            age_days = np.random.uniform(1, 20)
            burstiness = np.random.uniform(2.0, 8.0)
            mixer_exp = 0.0
            bridge_exp = 0.0
            dormant = 0.0

        elif role == "vasp_deposit":
            fan_in = np.random.randint(15, 60)
            fan_out = 1  # sweeps to hot wallet
            total_in = np.random.uniform(50000, 500000)
            total_out = total_in * 0.999
            pass_through = 0.999
            round_ratio = np.random.uniform(0.05, 0.3)
            age_days = np.random.uniform(30, 400)
            burstiness = np.random.uniform(8.0, 30.0)
            mixer_exp = 0.0
            bridge_exp = 0.1
            dormant = 0.0

        else: # mixer
            fan_in = np.random.randint(30, 200)
            fan_out = np.random.randint(30, 200)
            total_in = np.random.uniform(100000, 2000000)
            total_out = total_in * 0.98
            pass_through = 0.98
            round_ratio = np.random.uniform(0.8, 1.0)
            age_days = np.random.uniform(60, 900)
            burstiness = np.random.uniform(10.0, 50.0)
            mixer_exp = 1.0
            bridge_exp = 0.5
            dormant = 0.0

        data.append([
            fan_in, fan_out, total_in, total_out, pass_through,
            round_ratio, age_days, burstiness, mixer_exp, bridge_exp, dormant
        ])

    columns = [
        "fan_in", "fan_out", "total_in_usd", "total_out_usd", "pass_through_ratio",
        "round_amount_ratio", "age_days", "burstiness", "mixer_exposure", "bridge_exposure", "dormant_flag"
    ]
    return pd.DataFrame(data, columns=columns), pd.Series(labels)

def train_and_save_models():
    print("Training ChainNetra forensic ML models...")
    X, y = generate_synthetic_training_data(2000)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 1. Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    rf.fit(X_train, y_train)

    preds = rf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    cm = confusion_matrix(y_test, preds).tolist()
    classes = rf.classes_.tolist()

    rf_path = os.path.join(MODEL_DIR, "wallet_role_rf.joblib")
    joblib.dump(rf, rf_path)

    # 2. Isolation Forest Anomaly Detector
    iso = IsolationForest(contamination=0.12, random_state=42)
    iso.fit(X)
    iso_path = os.path.join(MODEL_DIR, "anomaly_iso.joblib")
    joblib.dump(iso, iso_path)

    # 3. Model Card Metrics
    metrics = {
        "model_name": "ChainNetra Wallet Role & Anomaly Classifier",
        "training_data_type": "Deterministic Synthetic Multi-Chain Forensic Patterns",
        "training_samples": len(X),
        "accuracy": round(float(acc), 4),
        "classes": classes,
        "confusion_matrix": cm,
        "feature_importances": dict(zip(X.columns.tolist(), [round(float(v), 4) for v in rf.feature_importances_])),
        "trained_at": pd.Timestamp.utcnow().isoformat()
    }
    metrics_path = os.path.join(MODEL_DIR, "model_card.json")
    import json
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Models successfully trained! Accuracy: {acc*100:.2f}%. Saved to {MODEL_DIR}")
    return metrics

if __name__ == "__main__":
    train_and_save_models()

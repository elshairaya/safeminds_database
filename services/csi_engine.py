

# SafeMinds CSI Inference Script
# Loads the trained CSI model and predicts CSI score from one user/session.


import numpy as np
import torch
import torch.nn as nn
import joblib


class SafeMindsCSINN(nn.Module):
    def __init__(self, input_size, hidden_layers, dropout_rate=0.3):
        super(SafeMindsCSINN, self).__init__()

        layers = []
        prev_size = input_size

        for i, hidden_size in enumerate(hidden_layers):
            layers.append(nn.Linear(prev_size, hidden_size))
            layers.append(nn.BatchNorm1d(hidden_size))
            layers.append(nn.LeakyReLU(0.1))

            if i < len(hidden_layers) - 1:
                layers.append(nn.Dropout(dropout_rate))

            prev_size = hidden_size

        layers.append(nn.Linear(prev_size, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


def load_csi_model(
    checkpoint_path="ml/safeminds_csi_model.pth",
    scaler_path="ml/safeminds_csi_scaler.pkl"
):
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    config = checkpoint["config"]
    input_size = checkpoint["input_size"]
    feature_names = checkpoint["feature_names"]

    model = SafeMindsCSINN(
        input_size=input_size,
        hidden_layers=config["hidden_layers"],
        dropout_rate=config["dropout"]
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    scaler = joblib.load(scaler_path)

    print("SafeMinds CSI model loaded successfully.")
    print(f"Device: {device}")
    print(f"Input size: {input_size}")
    print(f"Feature names: {feature_names}")

    return model, scaler, feature_names, device


def categorize_risk(score):
    if score < 20:
        return "low"
    elif score < 45:
        return "medium"
    else:
        return "high"


def generate_drivers(feature_dict):
    drivers = []

    if feature_dict.get("sleep_hours") is not None and feature_dict["sleep_hours"] < 6:
        drivers.append("Sleep duration was shorter than recommended")

    if feature_dict.get("sleep_hours") is not None and feature_dict["sleep_hours"] > 9:
        drivers.append("Sleep duration was longer than usual")

    if feature_dict.get("avg_hr") is not None and feature_dict["avg_hr"] > 85:
        drivers.append("Average heart rate was higher than expected")

    if feature_dict.get("insomnia_score") is not None and feature_dict["insomnia_score"] >= 10:
        drivers.append("Insomnia questionnaire score was elevated")

    if feature_dict.get("sleepiness_score") is not None and feature_dict["sleepiness_score"] >= 10:
        drivers.append("Daytime sleepiness score was elevated")

    if feature_dict.get("sleep_quality_composite") is not None and feature_dict["sleep_quality_composite"] < 40:
        drivers.append("Sleep quality composite score was low")

    if len(drivers) == 0:
        drivers.append("No major negative driver detected")

    return drivers


def generate_recommendations(drivers):
    recommendations = []

    for driver in drivers:
        lower_driver = driver.lower()

        if "sleep duration" in lower_driver:
            recommendations.append("Try to keep a consistent sleep schedule tonight")

        elif "heart rate" in lower_driver:
            recommendations.append("Monitor recovery and avoid intense activity close to bedtime")

        elif "insomnia" in lower_driver:
            recommendations.append("Track sleep difficulty trends over the next few days")

        elif "sleepiness" in lower_driver:
            recommendations.append("Monitor daytime sleepiness and compare it with recent sleep duration")

        elif "sleep quality" in lower_driver:
            recommendations.append("Review recent sleep consistency and nighttime interruptions")

    if len(recommendations) == 0:
        recommendations.append("Continue monitoring sleep and wellness trends")

    return list(dict.fromkeys(recommendations))


def predict_csi(model, scaler, feature_names, device, feature_dict):
    ordered_features = []

    for name in feature_names:
        value = feature_dict.get(name)

        if value is None:
            value = 0

        ordered_features.append(value)

    features = np.array(ordered_features, dtype=np.float32).reshape(1, -1)

    features_scaled = scaler.transform(features)
    features_tensor = torch.FloatTensor(features_scaled).to(device)

    model.eval()

    with torch.no_grad():
        prediction = model(features_tensor).cpu().numpy().flatten()[0]

    score = float(np.clip(prediction, 0, 100))
    risk_level = categorize_risk(score)
    drivers = generate_drivers(feature_dict)
    recommendations = generate_recommendations(drivers)

    return {
        "csi": int(round(score)),
        "risk_level": risk_level,
        "drivers": drivers,
        "recommendations": recommendations
    }

_model = None
_scaler = None
_feature_names = None
_device = None


def get_csi_prediction(feature_dict):
    global _model, _scaler, _feature_names, _device

    if _model is None:
        _model, _scaler, _feature_names, _device = load_csi_model()

    return predict_csi(
        model=_model,
        scaler=_scaler,
        feature_names=_feature_names,
        device=_device,
        feature_dict=feature_dict
    )


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

    session_type = (
        feature_dict.get("session_type")
        or feature_dict.get("sessionType")
        or ""
    )

    session_type = str(session_type).upper()

    avg_hr = feature_dict.get("avg_hr")
    sleep_hours = feature_dict.get("sleep_hours")
    insomnia_score = feature_dict.get("insomnia_score")
    sleepiness_score = feature_dict.get("sleepiness_score")
    sleep_quality = feature_dict.get("sleep_quality_composite")

    # Hourly check logic
    if session_type == "HOURLY_CHECK_SESSION":
        if avg_hr is not None:
            if avg_hr > 100:
                drivers.append("Heart rate was elevated during this hourly check")
            elif avg_hr < 50:
                drivers.append("Heart rate was lower than expected during this hourly check")
            else:
                drivers.append("Heart rate was within the expected range during this hourly check")

        if len(drivers) == 0:
            drivers.append("No major negative driver detected during this hourly check")

        return drivers

    # Night session logic
    if session_type == "NIGHT_SESSION":
        if sleep_hours is not None and sleep_hours < 6:
            drivers.append("Sleep duration was shorter than recommended")

        if sleep_hours is not None and sleep_hours > 9:
            drivers.append("Sleep duration was longer than usual")

        if avg_hr is not None and avg_hr > 85:
            drivers.append("Average heart rate was higher than expected during sleep")

        if insomnia_score is not None and insomnia_score >= 10:
            drivers.append("Insomnia questionnaire score was elevated")

        if sleepiness_score is not None and sleepiness_score >= 10:
            drivers.append("Daytime sleepiness score was elevated")

        if sleep_quality is not None and sleep_quality < 40:
            drivers.append("Sleep quality composite score was low")

        if len(drivers) == 0:
            drivers.append("No major negative driver detected during the night session")

        return drivers

    # Fallback logic if session type is missing or unknown
    if avg_hr is not None:
        if avg_hr > 100:
            drivers.append("Heart rate was elevated")
        elif avg_hr < 50:
            drivers.append("Heart rate was lower than expected")
        else:
            drivers.append("Heart rate was within the expected range")

    if len(drivers) == 0:
        drivers.append("No major negative driver detected")

    return drivers


def generate_recommendations(drivers):
    recommendations = []

    for driver in drivers:
        lower_driver = driver.lower()

        if "hourly check" in lower_driver:
            if "elevated" in lower_driver:
                recommendations.append("Take a short rest and continue monitoring your next readings")
            elif "lower than expected" in lower_driver:
                recommendations.append("Review this reading again if you feel unwell")
            elif "within the expected range" in lower_driver:
                recommendations.append("Continue normal monitoring")
            else:
                recommendations.append("Continue regular hourly monitoring")

        elif "sleep duration" in lower_driver:
            recommendations.append("Try to keep a consistent sleep schedule tonight")

        elif "heart rate" in lower_driver:
            recommendations.append("Monitor recovery and compare it with future readings")

        elif "insomnia" in lower_driver:
            recommendations.append("Track sleep difficulty trends over the next few days")

        elif "sleepiness" in lower_driver:
            recommendations.append("Monitor daytime sleepiness and compare it with recent sleep duration")

        elif "sleep quality" in lower_driver:
            recommendations.append("Review recent sleep consistency and nighttime interruptions")

    if len(recommendations) == 0:
        recommendations.append("Continue monitoring wellness trends")

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
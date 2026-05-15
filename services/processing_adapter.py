from datetime import datetime

from services.csi_engine import get_csi_prediction


MODEL_VERSION = "safeminds-csi-nn-v1"


def _safe_float(value, default=0.0):
    """
    Converts values safely to float.
    If value is None or invalid, returns the default.
    """
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_present(data, *names):
    """
    Returns the first attribute that exists and is not None.

    This supports both camelCase fields from mobile/watch
    and snake_case fields from Python/database models.
    """
    for name in names:
        value = getattr(data, name, None)
        if value is not None:
            return value
    return None


def _is_night_session(data):
    """
    Returns True if the session looks like a night/sleep session.
    Hourly check sessions should not be judged using full-night sleep rules.
    """

    session_type = _first_present(
        data,
        "sessionType",
        "session_type"
    )

    if session_type is None:
        # If session type is missing, assume night session for backward compatibility.
        return True

    session_type = str(session_type).upper()

    return session_type in [
        "NIGHT_SESSION",
        "SLEEP_SESSION",
        "SLEEP",
        "NIGHT"
    ]


def _calculate_sleep_hours_from_session(data):
    """
    Calculates sleep/session duration.

    Priority:
    1. Use sleep_hours / sleepHours if already provided.
    2. Otherwise calculate from sessionStart/sessionEnd.
    3. Return 0.0 if duration cannot be calculated.
    """

    direct_sleep_hours = _first_present(data, "sleep_hours", "sleepHours")

    if direct_sleep_hours is not None:
        return _safe_float(direct_sleep_hours, 0.0)

    session_start = _first_present(data, "sessionStart", "session_start")
    session_end = _first_present(data, "sessionEnd", "session_end")

    if session_start is None or session_end is None:
        return 0.0

    try:
        if isinstance(session_start, str):
            session_start = datetime.fromisoformat(
                session_start.replace("Z", "+00:00")
            )

        if isinstance(session_end, str):
            session_end = datetime.fromisoformat(
                session_end.replace("Z", "+00:00")
            )

        duration_seconds = (session_end - session_start).total_seconds()
        duration_hours = duration_seconds / 3600.0

        return max(0.0, duration_hours)

    except Exception:
        return 0.0


def _estimate_sleep_quality_from_movement(
    movement_variance,
    total_epochs,
    sleep_hours=None,
    is_night_session=True
):
    """
    Temporary proxy for sleep_quality_composite using watch movement data.

    Higher movement variance usually means more restless sleep,
    so the quality score is reduced.

    Hourly sessions should not be penalized using full-night sleep duration rules.

    This is not a clinical sleep quality score.
    It is only a first-version SafeMinds CSI feature.
    """

    movement_variance = _safe_float(movement_variance, 0.0)
    total_epochs = _safe_float(total_epochs, 0.0)
    sleep_hours = _safe_float(sleep_hours, 0.0)

    sleep_quality = 70.0

    # Penalize sleep duration only for night/sleep sessions.
    if is_night_session:
        if sleep_hours > 0 and sleep_hours < 6:
            sleep_quality -= 15.0

        if sleep_hours > 9:
            sleep_quality -= 10.0

    # Penalize restless movement.
    if movement_variance > 0:
        sleep_quality -= min(30.0, movement_variance * 10.0)

    # Penalize very short/incomplete night sessions only.
    if is_night_session and total_epochs > 0 and total_epochs < 4:
        sleep_quality -= 10.0

    return max(0.0, min(100.0, sleep_quality))


def build_csi_features(data):
    """
    Converts the real SafeMinds watch/mobile session object
    into the 10 features expected by the current CSI model.

    Current model features:
    - age
    - gender
    - bmi
    - avg_hr
    - sleep_hours
    - sleep_duration_risk
    - insomnia_score
    - sleepiness_score
    - chronotype_score
    - sleep_quality_composite

    Watch/session fields supported:
    - hrMean / hr_mean / heart_rate
    - movementVariance / movement_variance
    - totalEpochs / total_epochs
    - sessionStart / session_start
    - sessionEnd / session_end
    - sessionType / session_type

    Mobile profile/questionnaire fields supported:
    - age
    - gender
    - bmi
    - insomnia_score / insomniaScore
    - sleepiness_score / sleepinessScore
    - chronotype_score / chronotypeScore
    """

    is_night_session = _is_night_session(data)

    avg_hr = _safe_float(
        _first_present(data, "hrMean", "hr_mean", "heart_rate"),
        75.0
    )

    sleep_hours = _calculate_sleep_hours_from_session(data)

    if is_night_session:
        sleep_duration_risk = 1 if sleep_hours < 6 or sleep_hours > 9 else 0
    else:
        sleep_duration_risk = 0

    movement_variance = _first_present(
        data,
        "movementVariance",
        "movement_variance"
    )

    total_epochs = _first_present(
        data,
        "totalEpochs",
        "total_epochs"
    )

    sleep_quality_composite = _estimate_sleep_quality_from_movement(
        movement_variance=movement_variance,
        total_epochs=total_epochs,
        sleep_hours=sleep_hours,
        is_night_session=is_night_session
    )

    return {
        # Mobile profile features.
        # Defaults are temporary until mobile profile is connected.
        "age": _safe_float(
            _first_present(data, "age"),
            22.0
        ),
        "gender": _safe_float(
            _first_present(data, "gender"),
            1.0
        ),
        "bmi": _safe_float(
            _first_present(data, "bmi"),
            23.5
        ),

        # Watch-derived features.
        "avg_hr": avg_hr,
        "sleep_hours": sleep_hours,
        "sleep_duration_risk": sleep_duration_risk,

        # Mobile questionnaire features.
        # Defaults are temporary until questionnaire screens are connected.
        "insomnia_score": _safe_float(
            _first_present(data, "insomnia_score", "insomniaScore"),
            0.0
        ),
        "sleepiness_score": _safe_float(
            _first_present(data, "sleepiness_score", "sleepinessScore"),
            0.0
        ),
        "chronotype_score": _safe_float(
            _first_present(data, "chronotype_score", "chronotypeScore"),
            16.0
        ),

        # Watch movement proxy feature.
        "sleep_quality_composite": sleep_quality_composite
    }


def build_baseline_comparison(data, user_history):
    """
    Compares the current session with previous user sessions.

    user_history comes from ingest.py.
    This function supports both the new watch-based fields
    and the older database field names during transition.
    """

    current_session_id = _first_present(data, "session_id", "sessionId")

    current_sleep = _calculate_sleep_hours_from_session(data)

    current_hr = _safe_float(
        _first_present(data, "hrMean", "hr_mean", "heart_rate"),
        0.0
    )

    previous_records = []

    for record in user_history:
        record_session_id = _first_present(record, "session_id", "sessionId")

        if record_session_id == current_session_id:
            continue

        previous_records.append(record)

    if len(previous_records) == 0:
        return {
            "mode": "preliminary",
            "message": "Not enough previous data for personalized baseline yet.",
            "history_count": 0,
            "sleep_hours_change": None,
            "heart_rate_change": None
        }

    sleep_values = []
    hr_values = []

    for record in previous_records:
        record_sleep = _calculate_sleep_hours_from_session(record)

        record_hr = _safe_float(
            _first_present(record, "hrMean", "hr_mean", "heart_rate"),
            None
        )

        if record_sleep > 0:
            sleep_values.append(record_sleep)

        if record_hr is not None:
            hr_values.append(record_hr)

    avg_sleep = sum(sleep_values) / len(sleep_values) if sleep_values else None
    avg_hr = sum(hr_values) / len(hr_values) if hr_values else None

    sleep_change = (
        round(current_sleep - avg_sleep, 2)
        if avg_sleep is not None and current_sleep > 0
        else None
    )

    heart_rate_change = (
        round(current_hr - avg_hr, 2)
        if avg_hr is not None and current_hr > 0
        else None
    )

    return {
        "mode": "personalized" if len(previous_records) >= 7 else "preliminary",
        "message": "Baseline comparison calculated from previous sessions.",
        "history_count": len(previous_records),
        "avg_sleep_hours": round(avg_sleep, 2) if avg_sleep is not None else None,
        "avg_heart_rate": round(avg_hr, 2) if avg_hr is not None else None,
        "sleep_hours_change": sleep_change,
        "heart_rate_change": heart_rate_change
    }


def add_baseline_drivers(result, baseline_comparison):
    """
    Adds extra explainability based on the user's previous sessions.
    """

    drivers = list(result.get("drivers", []))

    sleep_change = baseline_comparison.get("sleep_hours_change")
    heart_rate_change = baseline_comparison.get("heart_rate_change")

    if sleep_change is not None and sleep_change <= -1:
        drivers.append("Sleep duration was lower than the user's recent baseline")

    if heart_rate_change is not None and heart_rate_change >= 8:
        drivers.append("Heart rate was higher than the user's recent baseline")

    return list(dict.fromkeys(drivers))


def run_processing(data, user_history):
    """
    Main processing function called by routes/ingest.py.

    It:
    1. Builds CSI model features from watch/mobile fields.
    2. Runs the SafeMinds CSI model.
    3. Builds baseline comparison from recent user history.
    4. Returns the exact format expected by routes/ingest.py.
    """

    features = build_csi_features(data)

    prediction = get_csi_prediction(features)

    baseline_comparison = build_baseline_comparison(data, user_history)

    drivers = add_baseline_drivers(prediction, baseline_comparison)

    return {
        "csi_score": prediction["csi"],
        "risk_level": prediction["risk_level"],
        "drivers": drivers,
        "recommendations": prediction["recommendations"],
        "baseline_comparison": baseline_comparison,
        "model_version": MODEL_VERSION
    }
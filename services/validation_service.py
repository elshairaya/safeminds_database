from datetime import datetime

def _first_present(data, *names):
    """
    Returns the first attribute that exists and is not None.
    Supports camelCase and snake_case fields.
    """
    for name in names:
        value = getattr(data, name, None)
        if value is not None:
            return value
    return None

def _safe_float(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
    
def _safe_int(value, default=None):
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default

def _parse_datetime(value):
    """
    Accepts datetime objects or ISO datetime strings.
    Returns datetime or None.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    return None

def _is_night_session(data):
    session_type = _first_present(data, "sessionType", "session_type")

    if session_type is None:
        return True

    session_type = str(session_type).upper()

    return session_type in [
        "NIGHT_SESSION",
        "SLEEP_SESSION",
        "SLEEP",
        "NIGHT"
    ]
def validate_sensor_data(data):
   # Validates the real SafeMinds watch/mobile session payload.

    user_id = _first_present(data, "user_id", "userId")
    if user_id is None or str(user_id).strip() == "":
        return False, "user_id is required"

    session_id = _first_present(data, "session_id", "sessionId")
    if session_id is None or str(session_id).strip() == "":
        return False, "session_id or sessionId is required"

    timestamp = _first_present(data, "timestamp")
    if _parse_datetime(timestamp) is None:
        return False, "timestamp must be a valid datetime"

    hr_mean = _safe_float(_first_present(data, "hrMean", "hr_mean"))
    if hr_mean is None:
        return False, "hrMean or hr_mean is required"

    if hr_mean < 30 or hr_mean > 220:
        return False, "hrMean/hr_mean must be between 30 and 220"

    hr_min = _safe_float(_first_present(data, "hrMin", "hr_min"))
    if hr_min is not None and (hr_min < 30 or hr_min > 220):
        return False, "hrMin/hr_min must be between 30 and 220"

    hr_max = _safe_float(_first_present(data, "hrMax", "hr_max"))
    if hr_max is not None and (hr_max < 30 or hr_max > 240):
        return False, "hrMax/hr_max must be between 30 and 240"

    if hr_min is not None and hr_max is not None and hr_min > hr_max:
        return False, "hrMin/hr_min cannot be greater than hrMax/hr_max"

    movement_variance = _safe_float(
        _first_present(data, "movementVariance", "movement_variance")
    )
    if movement_variance is None:
        return False, "movementVariance or movement_variance is required"

    if movement_variance < 0:
        return False, "movementVariance/movement_variance cannot be negative"

    movement_mean = _safe_float(
        _first_present(data, "movementMean", "movement_mean")
    )
    if movement_mean is not None and movement_mean < 0:
        return False, "movementMean/movement_mean cannot be negative"

    total_epochs = _safe_int(_first_present(data, "totalEpochs", "total_epochs"))
    if total_epochs is None:
        return False, "totalEpochs or total_epochs is required"

    if total_epochs < 0:
        return False, "totalEpochs/total_epochs cannot be negative"

    session_start = _parse_datetime(
        _first_present(data, "sessionStart", "session_start")
    )
    session_end = _parse_datetime(
        _first_present(data, "sessionEnd", "session_end")
    )

    if _is_night_session(data):
        if session_start is None:
            return False, "sessionStart/session_start is required for night sessions"

        if session_end is None:
            return False, "sessionEnd/session_end is required for night sessions"

        if session_end <= session_start:
            return False, "sessionEnd/session_end must be after sessionStart/session_start"

    return True, None
def dummy_processing(sensor_data, user_history):
    if sensor_data.heart_rate > 90 or sensor_data.sleep_hours < 5:
        return {
            "csi_score": 40,
            "risk_level": "high",
            "drivers": ["High heart rate or low sleep"],
            "recommendations": ["Rest more", "Do breathing exercise"],
            "baseline_comparison": {
                "heart_rate_change": "not_available",
                "sleep_change": "not_available"
            },
            "model_version": "dummy_v1"
        }

    return {
        "csi_score": 80,
        "risk_level": "low",
        "drivers": ["Stable vitals"],
        "recommendations": ["Keep your routine"],
        "baseline_comparison": {
            "heart_rate_change": "not_available",
            "sleep_change": "not_available"
        },
        "model_version": "dummy_v1"
    }


def run_processing(sensor_data, user_history):
    """
    This is the only function the backend route should call.

    Later, when TAREQ gives the real AI module,
    replace dummy_processing(...) with process_session(...).
    """
    return dummy_processing(sensor_data, user_history)
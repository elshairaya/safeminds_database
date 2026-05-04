def validate_sensor_data(data):
    if data.heart_rate < 30 or data.heart_rate > 220:
        return False, "heart_rate must be between 30 and 220"

    if data.spo2 < 70 or data.spo2 > 100:
        return False, "spo2 must be between 70 and 100"

    if data.sleep_hours < 0 or data.sleep_hours > 24:
        return False, "sleep_hours must be between 0 and 24"

    if data.stress_level < 0 or data.stress_level > 10:
        return False, "stress_level must be between 0 and 10"

    return True, None
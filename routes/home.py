from fastapi import APIRouter
from backend.database import SessionLocal
import backend.models as models

router = APIRouter()


def build_risk_description(risk_level: str):
    if risk_level == "HIGH":
        return "Significant changes were detected in your recent health patterns."
    if risk_level == "MEDIUM":
        return "Some changes were detected in your recent health patterns."
    return "Your recent health patterns look stable."


def get_activity_label(movement_mean):
    if movement_mean is None:
        return "UNKNOWN"

    movement_mean = float(movement_mean)

    if movement_mean < 0.15:
        return "LOW"
    if movement_mean < 0.6:
        return "MEDIUM"
    return "HIGH"


def get_sleep_efficiency(latest_reading):
    session_type = (latest_reading.session_type or "").upper()

    if session_type != "NIGHT_SESSION":
        return 0

    movement_variance = latest_reading.movement_variance or 0

    efficiency = 90 - min(30, movement_variance * 100)
    return round(max(0, min(100, efficiency)), 1)


def get_sleep_quality(sleep_efficiency):
    if sleep_efficiency is None or sleep_efficiency == 0:
        return "NOT_AVAILABLE"

    if sleep_efficiency >= 85:
        return "GOOD"
    if sleep_efficiency >= 70:
        return "FAIR"
    return "LOW"


def build_hr_zones(hr_min, hr_max, average_hr):
    hr_min = round(hr_min or 0)
    hr_max = round(hr_max or 0)
    average_hr = round(average_hr or 0)

    return [
        {
            "label": "Observed Range",
            "range": f"{hr_min}-{hr_max} bpm",
            "min": hr_min,
            "max": hr_max
        },
        {
            "label": "Average",
            "range": f"{average_hr} bpm",
            "min": average_hr,
            "max": average_hr
        }
    ]


def build_recommendation_objects(latest_csi):
    recs = latest_csi.recommendations or []
    drivers = latest_csi.drivers or []

    if not recs:
        return [
            {
                "type": "INFO",
                "title": "Continue monitoring",
                "description": "No specific recommendation is available for this session."
            }
        ]

    result = []

    for index, rec in enumerate(recs):
        description = drivers[index] if index < len(drivers) else rec

        result.append(
            {
                "type": "INFO",
                "title": rec,
                "description": description
            }
        )

    return result


@router.get("/home/latest")

def get_home_latest(user_id: str):
    db = SessionLocal()

    try:
        latest_csi = (
            db.query(models.CSIResult)
            .filter(models.CSIResult.user_id == user_id)
            .order_by(models.CSIResult.timestamp.desc())
            .first()
        )

        latest_reading = (
            db.query(models.SensorReading)
            .filter(models.SensorReading.user_id == user_id)
            .order_by(models.SensorReading.timestamp.desc())
            .first()
        )

        #added by shahed
        recent_readings=(
        db.query(models.SensorReading)
        .filter(models.SensorReading.user_id==user_id)
        .order_by(models.SensorReading.timestamp.desc())
        .limit(7)
        .all()
        )

        recent_readings=list(reversed(recent_readings))

        if latest_csi is None or latest_reading is None:
            return {
                "success": False,
                "message": "No home data found for this user"
            }

        risk_level = latest_csi.risk_level.upper()

        average_hr = latest_reading.hr_mean or 0
        hr_min = latest_reading.hr_min or 0
        hr_max = latest_reading.hr_max or 0
        movement_mean = latest_reading.movement_mean or 0
        movement_variance = latest_reading.movement_variance or 0
        total_epochs = latest_reading.total_epochs or 0

        activity_label = get_activity_label(movement_mean)
        sleep_efficiency = get_sleep_efficiency(latest_reading)
        sleep_quality = get_sleep_quality(sleep_efficiency)
        dynamic_recommendations = build_recommendation_objects(latest_csi)
        hr_zones = build_hr_zones(hr_min, hr_max, average_hr)

        # temporary estimate until real sleep duration is available
        sleep_hours = round(total_epochs * 30 / 3600, 1) if total_epochs else 0

        recommendations = dynamic_recommendations

        return {
            "success": True,
            "message": "Home data retrieved",
            "data": {
                "dashboard": {
                    "user_name": "User",
                    "csi_score": latest_csi.csi_score,
                    "risk_level": risk_level,
                    "risk_description": build_risk_description(risk_level),
                    "sleep_hours": sleep_hours,


                    "average_hr": average_hr,
                    #added by shahed
                    "heart_rate_chart":[
                    r.hr_mean or 0
                    for r in recent_readings
                    ],

                    #"steps": 0,
                    #added by shahed
                    "activity_level": movement_mean,
                    "activity_label": activity_label,
                    "activity_value": movement_mean,
                    "activity_chart": [
                    r.movement_mean or 0
                    for r in recent_readings
                    ],



                    "recommendations": recommendations
                },
                "sleep": {
                    "average_sleep_hours": sleep_hours,
                    "sleep_efficiency": sleep_efficiency,
                    "sleep_quality": sleep_quality,
                    "sleep_variability": latest_csi.baseline_comparison.get("sleep_hours_change", 0)
                    if isinstance(latest_csi.baseline_comparison, dict) else 0,
                    "movement_mean": movement_mean,
                    "movement_variance": movement_variance,
                    "total_epochs": total_epochs,
                    "weekly_sleep": [
                        {
                           # "day": latest_reading.timestamp.strftime("%a"),
                            #"hours": sleep_hours

                            #added by shahed
                            "day": r.timestamp.strftime("%a"),
                            "hours":round((r.total_epochs or 0) *30/3600,1)
                        }
                        for r in recent_readings
                    ],
                    "recommendations": dynamic_recommendations
                },
                "vitals": {
                    "average_hr": average_hr,
                    "resting_hr": hr_min,
                    "peak_hr": hr_max,
                    "hr_min": hr_min,
                    "hr_max": hr_max,
                    "activity_status": activity_label,
                    "weekly_hr": [
                        {
                           # "day": latest_reading.timestamp.strftime("%a"),
                            #"value": average_hr

                            #changed by shahed
                            "day": r.timestamp.strftime("%a"),
                            "value": r.hr_mean or 0
                        }
                        for r in recent_readings
                    ],
                    "hr_zones": hr_zones,
                    "recommendations": dynamic_recommendations
                },
                "activity": {
                    #"steps": 0,
                    "activity_level": movement_mean,
                    "activity_label": activity_label,
                    "movement_variance": movement_variance,

                #    "activity_level": "MEDIUM",
                 #   "movement_mean": movement_mean,
                   # "movement_variance": movement_variance,
                    #"weekly_steps": [
                    "weekly_activity" :[
                        {
                            "day": r.timestamp.strftime("%a"),
                            #latest_reading.timestamp.strftime("%a"),
                            #"steps": 0
                            "value": r.movement_mean or 0
                        }
                        for r in recent_readings
                    ]
                }
            }
        }

    finally:
        db.close()
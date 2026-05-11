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

        # temporary estimate until real sleep duration is available
        sleep_hours = round(total_epochs * 30 / 3600, 1) if total_epochs else 0

        recommendations = [
            {
                "type": "WARNING" if risk_level in ["MEDIUM", "HIGH"] else "GOOD",
                "title": latest_csi.recommendations[0] if latest_csi.recommendations else "Keep your routine",
                "description": latest_csi.drivers[0] if latest_csi.drivers else "Your recent health patterns are stable."
            }
        ]

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
                    "steps": 0,
                    "recommendations": recommendations
                },
                "sleep": {
                    "average_sleep_hours": sleep_hours,
                    "sleep_efficiency": 84,
                    "sleep_quality": "GOOD" if sleep_hours >= 6 else "LOW",
                    "sleep_variability": latest_csi.baseline_comparison.get("sleep_hours_change", 0)
                    if isinstance(latest_csi.baseline_comparison, dict) else 0,
                    "movement_mean": movement_mean,
                    "movement_variance": movement_variance,
                    "total_epochs": total_epochs,
                    "weekly_sleep": [
                        {
                            "day": latest_reading.timestamp.strftime("%a"),
                            "hours": sleep_hours
                        }
                    ],
                    "recommendations": [
                        {
                            "type": "INFO",
                            "title": "Maintain sleep routine",
                            "description": "Try sleeping and waking at consistent times."
                        }
                    ]
                },
                "vitals": {
                    "average_hr": average_hr,
                    "resting_hr": hr_min,
                    "peak_hr": hr_max,
                    "hr_min": hr_min,
                    "hr_max": hr_max,
                    "activity_level": "MEDIUM",
                    "weekly_hr": [
                        {
                            "day": latest_reading.timestamp.strftime("%a"),
                            "value": average_hr
                        }
                    ],
                    "hr_zones": [
                        {
                            "label": "Resting",
                            "range": "50-70 bpm",
                            "min": 50,
                            "max": 70
                        }
                    ],
                    "recommendations": [
                        {
                            "type": "GOOD",
                            "title": "Heart rate is stable",
                            "description": "Your heart rate is within your normal range."
                        }
                    ]
                },
                "activity": {
                    "steps": 0,
                    "activity_level": "MEDIUM",
                    "movement_mean": movement_mean,
                    "movement_variance": movement_variance,
                    "weekly_steps": [
                        {
                            "day": latest_reading.timestamp.strftime("%a"),
                            "steps": 0
                        }
                    ]
                }
            }
        }

    finally:
        db.close()
from fastapi import APIRouter
from backend.database import SessionLocal
import backend.models as models
from backend.schemas import SensorData
from services.processing_adapter import run_processing
from services.validation_service import validate_sensor_data
from datetime import datetime

router = APIRouter()

def _first_present(data, *names):
    for name in names:
        value = getattr(data, name, None)
        if value is not None:
            return value
    return None


@router.post("/ingest")
def ingest_data(data: SensorData):
    db = SessionLocal()

    try:
        # Convert milliseconds timestamp to datetime
        timestamp = datetime.fromtimestamp(data.timestamp / 1000)

        # Replace raw timestamp with converted datetime if needed
        data.timestamp = timestamp

        # Validation
        is_valid, error_message = validate_sensor_data(data)

        if not is_valid:
            return {
                "success": False,
                "message": "Invalid input",
                "error": error_message
            }
        
        session_id = _first_present(data, "session_id", "sessionId")

        existing_session = (
            db.query(models.SensorReading)
            .filter(models.SensorReading.session_id == session_id)
            .first()
        )

        if existing_session is not None:
            return {
                "success": False,
                "message": "Session already exists",
                "error": f"session_id '{session_id}' was already submitted"
            }

        sensor_record = models.SensorReading(
            user_id=data.user_id,
            session_id=session_id,
            timestamp=data.timestamp,

            session_type=_first_present(data, "session_type", "sessionType"),
            session_start=_first_present(data, "session_start", "sessionStart"),
            session_end=_first_present(data, "session_end", "sessionEnd"),

            hr_mean=_first_present(data, "hr_mean", "hrMean"),
            hr_min=_first_present(data, "hr_min", "hrMin"),
            hr_max=_first_present(data, "hr_max", "hrMax"),

            movement_mean=_first_present(data, "movement_mean", "movementMean"),
            movement_variance=_first_present(data, "movement_variance", "movementVariance"),
            total_epochs=_first_present(data, "total_epochs", "totalEpochs")
        )

        db.add(sensor_record)
        db.commit()

        user_history = (
            db.query(models.SensorReading)
            .filter(models.SensorReading.user_id == data.user_id)
            .order_by(models.SensorReading.timestamp.desc())
            .limit(10)
            .all()
        )

        result = run_processing(data, user_history)

        csi_record = models.CSIResult(
            user_id=data.user_id,
            session_id=session_id,
            timestamp=data.timestamp,
            csi_score=result["csi_score"],
            risk_level=result["risk_level"],
            drivers=result["drivers"],
            recommendations=result["recommendations"],
            baseline_comparison=result["baseline_comparison"],
            model_version=result["model_version"]
        )

        db.add(csi_record)
        db.commit()

        return {
     "success": True,
     "message": "Session ingested successfully",
     "csi": {
        "user_id": data.user_id,
        "session_id": data.session_id,
        "timestamp": data.timestamp.isoformat(),
        "csi_score": result["csi_score"],
        "risk_level": result["risk_level"].upper(),
        "drivers": result["drivers"],
        "recommendations": result["recommendations"],
        "baseline_comparison": result["baseline_comparison"],
        "model_version": result["model_version"]
    }
}

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": "Server error",
            "error": str(e)
        }

    finally:
        db.close()
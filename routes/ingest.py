from fastapi import APIRouter
from backend.database import SessionLocal
import backend.models as models
from backend.schemas import SensorData
from services.processing_adapter import run_processing
from services.validation_service import validate_sensor_data

router = APIRouter()


@router.post("/ingest")
def ingest_data(data: SensorData):
    db = SessionLocal()

    try:
        is_valid, error_message = validate_sensor_data(data)

        if not is_valid:
            return {
                "success": False,
                "message": "Invalid input",
                "error": error_message
            }

        existing_session = (
            db.query(models.SensorReading)
            .filter(models.SensorReading.session_id == data.session_id)
            .first()
        )

        if existing_session is not None:
            return {
                "success": False,
                "message": "Session already exists",
                "error": f"session_id '{data.session_id}' was already submitted"
            }

        sensor_record = models.SensorReading(
            user_id=data.user_id,
            session_id=data.session_id,
            timestamp=data.timestamp,
            heart_rate=data.heart_rate,
            spo2=data.spo2,
            steps=data.steps,
            sleep_hours=data.sleep_hours,
            stress_level=data.stress_level
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
            session_id=data.session_id,
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
            "message": "Data saved and processed successfully",
            "csi": result
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Server error",
            "error": str(e)
        }

    finally:
        db.close()
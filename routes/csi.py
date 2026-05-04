from fastapi import APIRouter
from backend.database import SessionLocal
import backend.models
from typing import Optional
from datetime import datetime
router = APIRouter()


@router.get("/csi/latest")
def get_latest_csi(user_id: str):
    db = SessionLocal()

    try:
        latest = (
            db.query(backend.models.CSIResult)
            .filter(backend.models.CSIResult.user_id == user_id)
            .order_by(backend.models.CSIResult.timestamp.desc())
            .first()
        )

        if latest is None:
            return {
                "success": False,
                "message": "No CSI result found for this user"
            }

        return {
            "success": True,
            "data": {
                "user_id": latest.user_id,
                "session_id": latest.session_id,
                "timestamp": latest.timestamp,
                "csi_score": latest.csi_score,
                "risk_level": latest.risk_level,
                "drivers": latest.drivers,
                "recommendations": latest.recommendations,
                "baseline_comparison": latest.baseline_comparison,
                "model_version": latest.model_version
            }
        }

    finally:
        db.close()


@router.get("/csi/history")
def get_csi_history(
    user_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None
):
    db = SessionLocal()

    try:
        query = db.query(backend.models.CSIResult).filter(
            backend.models.CSIResult.user_id == user_id
        )

        if from_date:
            query = query.filter(backend.models.CSIResult.timestamp >= from_date)

        if to_date:
            query = query.filter(backend.models.CSIResult.timestamp <= to_date)

        results = query.order_by(backend.models.CSIResult.timestamp.desc()).all()

        if not results:
            return {
                "success": False,
                "message": "No history found for this user"
            }

        history = []

        for result in results:
            history.append({
                "timestamp": result.timestamp,
                "csi_score": result.csi_score,
                "risk_level": result.risk_level
            })

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "history": history
            }
        }

    finally:
        db.close()
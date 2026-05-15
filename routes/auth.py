from fastapi import APIRouter
from passlib.context import CryptContext
from backend.database import SessionLocal
import backend.models as models
from backend.schemas import UserSignup, UserLogin
import uuid

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/signup")
def signup(data: UserSignup):
    db = SessionLocal()

    try:
        existing_user = (
            db.query(models.User)
            .filter(models.User.username == data.username)
            .first()
        )

        if existing_user:
            return {
                "success": False,
                "message": "Username already exists"
            }

        new_user = models.User(
            user_id=str(uuid.uuid4()),
            username=data.username,
            full_name=data.full_name,
            password_hash=pwd_context.hash(data.password),
            age_range=data.age_range,
            gender=data.gender,

            #added by Shahed
            height=data.height,
            weight=data.weight
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "success": True,
            "message": "User created successfully",
            "data": {
                "user_id": new_user.user_id,
                "username": new_user.username,
                "full_name": new_user.full_name
            }
        }

    finally:
        db.close()


@router.post("/login")
def login(data: UserLogin):
    db = SessionLocal()

    try:
        user = (
            db.query(models.User)
            .filter(models.User.username == data.username)
            .first()
        )

        if not user:
            return {
                "success": False,
                "message": "Invalid username or password"
            }

        if not pwd_context.verify(data.password, user.password_hash):
            return {
                "success": False,
                "message": "Invalid username or password"
            }

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "user_id": user.user_id,
                "username": user.username,
                "full_name": user.full_name
            }
        }

    finally:
        db.close()
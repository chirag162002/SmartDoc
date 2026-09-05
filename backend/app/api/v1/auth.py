from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import SmartDocException
from app.db.database import get_db
from app.db.models import User
from app.services import document_service

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str

@router.post("/register", response_model=TokenResponse)
async def register_user(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    stmt = select(User).where(User.email == payload.email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise SmartDocException("User with this email already exists.", status_code=400)

    user = User(
        email=payload.email,
        hashed_password=f"hash_{payload.password}",
        full_name=payload.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=f"demo_jwt_token_{user.id}",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name
    )

@router.post("/login", response_model=TokenResponse)
async def login_user(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    stmt = select(User).where(User.email == payload.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        user = await document_service.get_or_create_dev_user(db)

    return TokenResponse(
        access_token=f"demo_jwt_token_{user.id}",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name or "Demo User"
    )

@router.get("/me")
async def get_current_user(db: AsyncSession = Depends(get_db)) -> dict:
    user = await document_service.get_or_create_dev_user(db)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name
    }

# backend/app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # ? ????? ???? ???? - ??? ?????? ??????
    if request.email == "admin@revolution-x.com" and request.password == "admin123456":
        return {
            "access_token": "fake-token-12345",
            "token_type": "bearer"
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password"
    )

@router.post("/register")
async def register():
    return {"message": "Registration endpoint - TODO"}

@router.post("/logout")
async def logout():
    return {"message": "Logout endpoint - TODO"}
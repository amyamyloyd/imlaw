from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    """User model for authentication"""
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: bool = False
    role: str = "user"
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user"""
    # TODO: Implement proper JWT token validation
    # For now, return a mock user for development
    return User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        role="admin"
    ) 
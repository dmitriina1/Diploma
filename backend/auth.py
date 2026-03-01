"""
Authentication & Authorization module
=====================================
JWT-based auth for Interview Prep API.

Roles:
- user: registered user, can access trainer, recordings, assignments
- admin: full access including admin panel

Default admin: admin/admin (created on startup)
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from jose import JWTError, jwt
from passlib.context import CryptContext
import asyncpg

# ============== Configuration ==============
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "interview-prep-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://diploma:diploma123@localhost:5432/interview_prep")

# ============== Password Hashing ==============
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============== Security ==============
security = HTTPBearer(auto_error=False)


# ============== Pydantic Models ==============
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    role: str


# ============== Helper Functions ==============
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ============== Database Operations ==============
async def create_users_table():
    """Create users table and seed admin user"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                display_name VARCHAR(100),
                role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
                is_active BOOLEAN DEFAULT TRUE,
                avatar_url TEXT,
                github_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        """)
        
        # Add new columns if upgrading from older schema
        for col, typ in [("avatar_url", "TEXT"), ("github_url", "VARCHAR(500)")]:
            try:
                await conn.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {typ}")
            except Exception:
                pass
        
        # Seed admin user (admin/admin)
        existing = await conn.fetchval("SELECT id FROM users WHERE username = 'admin'")
        if not existing:
            admin_hash = hash_password("admin")
            await conn.execute(
                """INSERT INTO users (username, password_hash, display_name, role)
                   VALUES ('admin', $1, 'Администратор', 'admin')""",
                admin_hash
            )
            print("✅ Admin user created (admin/admin)")
        else:
            print("✅ Admin user already exists")
        
        print("✅ Users table ensured")
    finally:
        await conn.close()


async def get_user_by_username(username: str) -> Optional[dict]:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            "SELECT id, username, password_hash, display_name, role, is_active FROM users WHERE username = $1",
            username
        )
        return dict(row) if row else None
    finally:
        await conn.close()


async def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            "SELECT id, username, display_name, role, is_active, avatar_url, github_url, created_at FROM users WHERE id = $1",
            user_id
        )
        if row:
            d = dict(row)
            for k in d:
                if hasattr(d[k], 'isoformat'):
                    d[k] = d[k].isoformat()
            return d
        return None
    finally:
        await conn.close()


async def update_user_profile(user_id: int, display_name: str = None, github_url: str = None, avatar_url: str = None) -> Optional[dict]:
    """Update user profile fields"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        sets = []
        params = []
        idx = 1

        if display_name is not None:
            sets.append(f"display_name = ${idx}")
            params.append(display_name)
            idx += 1
        if github_url is not None:
            sets.append(f"github_url = ${idx}")
            params.append(github_url)
            idx += 1
        if avatar_url is not None:
            sets.append(f"avatar_url = ${idx}")
            params.append(avatar_url)
            idx += 1

        if not sets:
            return await get_user_by_id(user_id)

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(sets)} WHERE id = ${idx} RETURNING id, username, display_name, role, is_active, avatar_url, github_url, created_at"
        row = await conn.fetchrow(query, *params)
        if row:
            d = dict(row)
            for k in d:
                if hasattr(d[k], 'isoformat'):
                    d[k] = d[k].isoformat()
            return d
        return None
    finally:
        await conn.close()


async def create_user(username: str, password: str, display_name: str = None) -> dict:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        existing = await conn.fetchval("SELECT id FROM users WHERE username = $1", username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким логином уже существует"
            )
        
        password_hash = hash_password(password)
        row = await conn.fetchrow(
            """INSERT INTO users (username, password_hash, display_name, role)
               VALUES ($1, $2, $3, 'user')
               RETURNING id, username, display_name, role""",
            username, password_hash, display_name or username
        )
        return dict(row)
    finally:
        await conn.close()


async def update_last_login(user_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
            user_id
        )
    finally:
        await conn.close()


# ============== FastAPI Dependencies ==============
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """
    Get current user from JWT token. Returns None if not authenticated.
    Use this for optional auth (some features available without login).
    """
    if not credentials:
        return None
    
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = await get_user_by_id(int(user_id))
    if not user or not user.get("is_active"):
        return None
    
    return user


async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Require authenticated user. Raises 401 if not authenticated.
    Use for routes that require login (trainer, recordings, assignments).
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или истёкший токен",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = await get_user_by_id(int(user_id))
    if not user or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или деактивирован"
        )
    
    return user


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    """
    Require admin role. Raises 403 if not admin.
    Use for admin-only routes.
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Требуются права администратора."
        )
    return user

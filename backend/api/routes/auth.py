import asyncpg
from fastapi import APIRouter, Body, Depends, HTTPException, status

from auth import (
    TokenResponse,
    UserLogin,
    UserRegister,
    create_access_token,
    create_user,
    get_user_by_username,
    require_auth,
    update_last_login,
    update_user_profile,
    verify_password,
)
from core.config import DATABASE_URL


router = APIRouter(tags=["Auth"])


@router.post("/api/auth/register", response_model=TokenResponse)
async def register(data: UserRegister):
    user = await create_user(data.username, data.password, data.display_name)
    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    await update_last_login(user["id"])
    return TokenResponse(
        access_token=token,
        user={
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
        },
    )


@router.post("/api/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await get_user_by_username(data.username)

    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль"
        )

    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован"
        )

    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    await update_last_login(user["id"])

    return TokenResponse(
        access_token=token,
        user={
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
        },
    )


@router.get("/api/auth/me")
async def get_me(user: dict = Depends(require_auth)):
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "avatar_url": user.get("avatar_url"),
        "github_url": user.get("github_url"),
        "created_at": user.get("created_at"),
    }


@router.get("/api/profile")
async def get_profile(user: dict = Depends(require_auth)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        bookmarks = await conn.fetch(
            """
            SELECT b.id, b.note, b.created_at,
                   q.id as question_id, q.question, q.topic, q.difficulty
            FROM bookmarks b
            JOIN questions q ON b.question_id = q.id
            WHERE b.user_session = $1
            ORDER BY b.created_at DESC
            LIMIT 50
        """,
            user["username"],
        )

        bookmarks_list = []
        for b in bookmarks:
            row = dict(b)
            for k in row:
                if hasattr(row[k], "isoformat"):
                    row[k] = row[k].isoformat()
            bookmarks_list.append(row)

        try:
            trainer_stats = await conn.fetchrow(
                """
                SELECT COUNT(*) as total_cards,
                       COUNT(*) FILTER (WHERE repetitions > 0) as reviewed,
                       ROUND(AVG(easiness_factor)::numeric, 2) as avg_easiness
                FROM sr_cards
                WHERE user_session = $1
            """,
                user["username"],
            )
            trainer_stats = dict(trainer_stats) if trainer_stats else None
            if trainer_stats and trainer_stats.get("avg_easiness") is not None:
                trainer_stats["avg_easiness"] = float(trainer_stats["avg_easiness"])
        except Exception:
            trainer_stats = None

        return {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
            "avatar_url": user.get("avatar_url"),
            "github_url": user.get("github_url"),
            "created_at": user.get("created_at"),
            "bookmarks": bookmarks_list,
            "trainer_stats": trainer_stats,
        }
    finally:
        await conn.close()


@router.put("/api/profile")
async def update_profile(data: dict = Body(...), user: dict = Depends(require_auth)):
    updated = await update_user_profile(
        user_id=user["id"],
        display_name=data.get("display_name"),
        github_url=data.get("github_url"),
        avatar_url=data.get("avatar_url"),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {
        "id": updated["id"],
        "username": updated["username"],
        "display_name": updated["display_name"],
        "role": updated["role"],
        "avatar_url": updated.get("avatar_url"),
        "github_url": updated.get("github_url"),
        "created_at": updated.get("created_at"),
        "message": "Профиль обновлён",
    }

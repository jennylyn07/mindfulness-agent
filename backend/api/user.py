"""
MindFlow — User profile route.
Returns the user document (displayName, preferences, etc.) from Cosmos.
Used by the frontend to show the user's name without hardcoding.
"""
from fastapi import APIRouter, HTTPException
from backend.providers import cosmos_repository as db

router = APIRouter()

_DEMO_USER_ID = "demo-user-001"


@router.get("/user")
async def get_user(userId: str = _DEMO_USER_ID):
    """Return user profile — displayName, email, preferences."""
    try:
        user = await db.get_user(userId)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "userId": user.get("userId", userId),
            "displayName": user.get("displayName", ""),
            "email": user.get("email", ""),
            "preferences": user.get("preferences", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
MindFlow — FastAPI Backend
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.api import chat, habits, mood, journal, insights, user, grove, calendar

# Load backend/.env relative to this file — safe regardless of CWD
import os as _os
from dotenv import load_dotenv as _load_dotenv
_load_dotenv(dotenv_path=_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".env"), override=True)

app = FastAPI(title="MindFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT"],
    allow_headers=["Content-Type"],
)

# ── Routers ────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(habits.router)
app.include_router(user.router)
app.include_router(mood.router)
app.include_router(journal.router)
app.include_router(insights.router)
app.include_router(grove.router)
app.include_router(calendar.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MindFlow API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

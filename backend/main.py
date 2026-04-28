"""
MindFlow — FastAPI Backend
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.api import chat, habits, mood

load_dotenv()

app = FastAPI(title="MindFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)

# ── Routers ────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(habits.router)
app.include_router(mood.router)
# journal.router — added Hour 5 (GET /journal)
# insights.router — added Hour 7 (GET /insights)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MindFlow API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

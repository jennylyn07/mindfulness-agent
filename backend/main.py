"""
MindFlow — FastAPI Backend
Placeholder for Hour 1. Full agent pipeline implemented in Hours 2–8.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MindFlow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MindFlow API"}


# Routes registered in Hours 3–8:
# from backend.api import chat, habits, mood, journal, insights
# app.include_router(chat.router)
# app.include_router(habits.router)
# app.include_router(mood.router)
# app.include_router(journal.router)
# app.include_router(insights.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

"""
MindFlow — Pydantic Schemas
All data models for the 5 Cosmos DB collections + API request/response types.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Cosmos Collection Models ───────────────────────────────

class UserPreferences(BaseModel):
    morningCheckIn: bool = True
    tone: str = "warm"


class User(BaseModel):
    id: str
    userId: str
    email: str
    displayName: str
    timezone: str = "UTC"
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    createdAt: str


class MemoryFact(BaseModel):
    content: str
    source: str                  # "journal_entry" | "mood_log" | "habit_log"
    importance: float            # 0.0 – 1.0
    createdAt: str
    lastReferencedAt: str


class LearnedPreferences(BaseModel):
    preferredTone: str = "warm"
    bestJournalingTime: str = "evening"
    respondsWellTo: list[str] = Field(default_factory=list)
    avoids: list[str] = Field(default_factory=list)


class UserMemory(BaseModel):
    id: str                      # == userId (one doc per user)
    userId: str
    facts: list[MemoryFact] = Field(default_factory=list)
    weekSummary: str = ""
    weekSummaryUpdatedAt: str = ""
    learnedPreferences: LearnedPreferences = Field(default_factory=LearnedPreferences)
    recurringThemes: list[str] = Field(default_factory=list)
    breakthroughs: list[str] = Field(default_factory=list)
    updatedAt: str = ""


class JournalEntry(BaseModel):
    id: str
    userId: str
    content: str
    moodAtEntry: str
    sentiment: str               # "positive" | "neutral" | "negative"
    themes: list[str] = Field(default_factory=list)
    summary: str = ""
    agentUsed: str = "journal"
    embedding: list[float] = Field(default_factory=list)
    timestamp: str


class HabitLog(BaseModel):
    id: str
    userId: str
    name: str
    why: str
    frequency: str = "daily"
    targetTime: str = ""
    durationMins: int = 0
    logs: list[str] = Field(default_factory=list)   # ["2026-04-28", ...]
    currentStreak: int = 0
    longestStreak: int = 0
    active: bool = True


class MoodLog(BaseModel):
    id: str
    userId: str
    mood: str                    # "anxious" | "sad" | "okay" | "good" | "great"
    score: int                   # 1–10
    context: str = "general"     # "morning_checkin" | "evening_checkin" | "general"
    note: str = ""
    timestamp: str


# ── API Request / Response Models ─────────────────────────

class ChatRequest(BaseModel):
    message: str
    userId: str = "demo-user-001"
    conversationHistory: list[dict] = Field(default_factory=list)
    agentOverride: Optional[str] = None   # e.g. "habit" — skips orchestrator


class OrchestratorResult(BaseModel):
    agent: str                   # "mindfulness" | "journal" | "habit" | "insights"
    confidence: float
    mood: str
    urgency: str                 # "low" | "medium" | "high"


class HabitCreate(BaseModel):
    name: str
    why: str
    frequency: str = "daily"
    targetTime: str = ""
    durationMins: int = 0
    userId: str = "demo-user-001"


class MoodLogRequest(BaseModel):
    mood: str
    score: int
    context: str = "general"
    note: str = ""
    userId: str = "demo-user-001"


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    why: Optional[str] = None
    targetTime: Optional[str] = None
    durationMins: Optional[int] = None
    frequency: Optional[str] = None

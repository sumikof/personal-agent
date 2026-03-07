"""FastAPI アプリケーションエントリポイント。"""
from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.tasks import router as tasks_router
from app.chat.router import router as chat_router

app = FastAPI(
    title="Personal Agent API",
    description="チャットで話しかけるだけで Redmine タスク管理を代行するパーソナル AI エージェント",
    version="1.0.0",
)

app.include_router(chat_router)
app.include_router(tasks_router)

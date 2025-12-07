import asyncio
import json
import logging
import sqlite3
from typing import List, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_db_path
from backend.service.main_service import CryptoAlphaService

app = FastAPI(title="Crypto Alpha Scout")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = CryptoAlphaService()
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def _db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/health")
async def health():
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/projects")
async def list_projects(limit: int = 100) -> List[Dict[str, Any]]:
    conn = _db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, category, source, discovered_at, confidence_score, verdict, status
        FROM projects
        ORDER BY discovered_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/projects/{project_id}")
async def get_project(project_id: str) -> Dict[str, Any]:
    conn = _db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM projects WHERE id = ?
        """,
        (project_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"error": "not_found"}
    data = dict(row)
    try:
        data["llm_analysis"] = json.loads(data.get("llm_analysis") or "{}")
    except Exception:
        data["llm_analysis"] = {}
    return data


@app.post("/scan")
async def trigger_scan():
    logger.info("Manual scan requested")
    asyncio.create_task(service.scan_and_analyze())
    return {"status": "scheduled"}

import aiohttp
import asyncio
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Any

from backend.config import get_db_path, get_scanner_config
from backend.bot.telegram_logger import log_detailed
from backend.telegram_client import send_message as send_telegram_message


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


class CryptoTracker:
    """Сканер крипто-проектов из разных источников."""

    def __init__(self):
        self.db_path = get_db_path()
        _ensure_dir(self.db_path)
        self.cfg = get_scanner_config()
        self.init_database()

    def init_database(self):
        """Инициализация SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                source TEXT,
                description TEXT,
                discovered_at TIMESTAMP,
                raw_data TEXT,
                status TEXT DEFAULT 'new',
                llm_analysis TEXT,
                confidence_score REAL,
                verdict TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                event_type TEXT,
                event_data TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
            """
        )
        conn.commit()
        conn.close()

    async def scan_github(self) -> List[Dict[str, Any]]:
        """Сканирование GitHub search API."""
        sources_cfg = self.cfg.get("sources", {})
        if not sources_cfg.get("github", {}).get("enabled", True):
            return []

        urls = [
            "https://api.github.com/search/repositories?q=crypto+language:solidity&sort=updated",
            "https://api.github.com/search/repositories?q=defi+language:rust&sort=updated",
            "https://api.github.com/search/repositories?q=nft+language:javascript&sort=updated",
        ]

        projects: List[Dict[str, Any]] = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status != 200:
                            await log_detailed(
                                "SCAN",
                                "github_error",
                                data=url,
                                status=str(response.status),
                                level="WARNING",
                            )
                            continue
                        data = await response.json()
                        batch_count = 0
                        for repo in data.get("items", [])[:10]:
                            projects.append(
                                {
                                    "id": f"github_{repo['id']}",
                                    "name": repo.get("name"),
                                    "description": repo.get("description"),
                                    "category": "Infrastructure",
                                    "source": "github",
                                    "raw_data": repo,
                                    "url": repo.get("html_url"),
                                }
                            )
                            batch_count += 1
                        await log_detailed(
                            "SCAN",
                            "github_ok",
                            data=url,
                            status=f"items={batch_count}",
                        )
                except Exception as e:
                    print(f"Error scanning GitHub: {e}")
                    await log_detailed(
                        "SCAN",
                        "github_exception",
                        data=url,
                        status=str(e),
                        level="ERROR",
                    )
        return projects

    async def scan_defi_llama(self) -> List[Dict[str, Any]]:
        """Новые протоколы DeFi Llama (≤7 дней)."""
        sources_cfg = self.cfg.get("sources", {})
        if not sources_cfg.get("defillama", {}).get("enabled", True):
            return []

        url = "https://api.llama.fi/protocols"
        projects: List[Dict[str, Any]] = []

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        await log_detailed(
                            "SCAN",
                            "defillama_error",
                            data=url,
                            status=str(response.status),
                            level="WARNING",
                        )
                        return []
                    data = await response.json()
                    for protocol in data:
                        listed = protocol.get("listedAt")
                        if not listed:
                            continue
                        listed_date = datetime.fromtimestamp(listed, tz=timezone.utc)
                        days_ago = (datetime.now(tz=timezone.utc) - listed_date).days
                        if days_ago <= 7:
                            projects.append(
                                {
                                    "id": f"defillama_{protocol.get('slug')}",
                                    "name": protocol.get("name"),
                                    "category": "DeFi",
                                    "source": "defillama",
                                    "raw_data": protocol,
                                    "url": protocol.get("url"),
                                    "description": protocol.get("description"),
                                }
                            )
                    await log_detailed(
                        "SCAN",
                        "defillama_ok",
                        data="new protocols",
                        status=f"count={len(projects)}",
                    )
            except Exception as e:
                print(f"Error scanning DeFi Llama: {e}")
                await log_detailed(
                    "SCAN",
                    "defillama_exception",
                    data=url,
                    status=str(e),
                    level="ERROR",
                )
        return projects

    async def run_full_scan(self) -> Dict[str, Any]:
        """Полное сканирование (параллельно по источникам)."""
        await log_detailed("SCAN", "run_full_scan_start")
        await send_telegram_message("🛰️ Запуск сканирования источников")
        tasks = [self.scan_github(), self.scan_defi_llama()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_projects: List[Dict[str, Any]] = []
        source_counts: Dict[str, int] = {}
        for result in results:
            if isinstance(result, list):
                all_projects.extend(result)
                for p in result:
                    src = p.get("source", "unknown")
                    source_counts[src] = source_counts.get(src, 0) + 1
        await log_detailed(
            "SCAN",
            "run_full_scan_done",
            status=f"total={len(all_projects)}",
            details={"sources": source_counts},
        )
        await send_telegram_message(
            f"🛰️ Сканирование завершено, найдено {len(all_projects)} проектов\n"
            + "\n".join(f"• {k}: {v}" for k, v in source_counts.items())
        )
        await self.save_projects(all_projects)
        return {"projects": all_projects, "source_counts": source_counts}

    async def save_projects(self, projects: List[Dict[str, Any]]) -> None:
        """Сохранение проектов в БД."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for project in projects:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO projects
                    (id, name, category, source, description, discovered_at, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project.get("id"),
                        project.get("name", "Unknown"),
                        project.get("category", "uncategorized"),
                        project.get("source", "unknown"),
                        project.get("description"),
                        datetime.now(tz=timezone.utc).isoformat(),
                        json.dumps(project.get("raw_data", {})),
                    ),
                )
            except Exception as e:
                print(f"Error saving project {project.get('id')}: {e}")
                await log_detailed(
                    "SCAN",
                    "save_project_error",
                    data=str(project.get("id")),
                    status=str(e),
                    level="ERROR",
                )
        conn.commit()
        conn.close()

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import schedule

from backend.analyzer.openrouter_analyzer import OpenRouterAnalyzer
from backend.analyzer.strategy_generator import StrategyGenerator
from backend.config import get_db_path, get_notifications_config, get_scanner_config
from backend.scanner.crypto_scanner import CryptoTracker
from backend.telegram_client import send_message as send_telegram_message


class CryptoAlphaService:
    """
    Сервис: сканирование источников -> анализ через OpenRouter -> уведомления.
    """

    def __init__(self):
        self.tracker = CryptoTracker()
        self.analyzer = OpenRouterAnalyzer()
        self.strategy_gen = StrategyGenerator()
        self.notifications_cfg = get_notifications_config()
        self.scan_cfg = get_scanner_config()
        self.running = False

    # ---------------- DB helpers ---------------- #
    def _open_db(self):
        return sqlite3.connect(get_db_path())

    async def get_unanalyzed_projects(self) -> List[Dict[str, Any]]:
        conn = self._open_db()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM projects
            WHERE status = 'new'
            ORDER BY discovered_at DESC
            LIMIT 50
            """
        )
        rows = cursor.fetchall()
        conn.close()

        projects: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            try:
                item["raw_data"] = json.loads(item.get("raw_data") or "{}")
            except Exception:
                item["raw_data"] = {}
            projects.append(item)
        return projects

    async def save_analysis(self, project_id: str, analysis: Dict[str, Any]):
        conn = self._open_db()
        cursor = conn.cursor()
        score = analysis.get("score", 0)
        verdict = analysis.get("verdict")
        try:
            cursor.execute(
                """
                UPDATE projects
                SET status = 'analyzed',
                    llm_analysis = ?,
                    confidence_score = ?,
                    verdict = ?
                WHERE id = ?
                """,
                (json.dumps(analysis), score, verdict, project_id),
            )
            cursor.execute(
                """
                INSERT INTO events (project_id, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    project_id,
                    "llm_analysis_completed",
                    json.dumps(analysis),
                    datetime.now(tz=timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        except Exception as e:
            print(f"Error saving analysis: {e}")
            conn.rollback()
        finally:
            conn.close()

    # ---------------- Notifications ---------------- #
    async def _notify_error(self, message: str):
        await send_telegram_message(f"⚠️ Ошибка: {message}")

    async def _notify_scan_complete(self):
        await send_telegram_message("✅ Сканирование завершено.")

    async def should_notify(self, analysis: Dict[str, Any]) -> bool:
        telegram_cfg = self.notifications_cfg.get("telegram", {})
        if not telegram_cfg.get("enabled", False):
            return False
        score = analysis.get("score", 0)
        verdict = (analysis.get("verdict") or "").upper()
        threshold = telegram_cfg.get("alert_threshold", 8.0)
        if score >= threshold:
            return True
        if verdict in {"STRONG_BUY", "BUY", "SCAM"}:
            return True
        return False

    async def send_notification(self, project: Dict[str, Any], analysis: Dict[str, Any]):
        try:
            from backend.bot.telegram_bot import TelegramBot
        except ImportError:
            await send_telegram_message("Telegram bot dependency missing.")
            return

        telegram_cfg = self.notifications_cfg.get("telegram", {})
        if not telegram_cfg.get("enabled", False):
            return

        bot = TelegramBot(
            bot_token=telegram_cfg.get("token", ""),
            chat_id=telegram_cfg.get("chat_id", ""),
        )
        await bot.send_project_analysis(project, analysis)

    # ---------------- Core workflow ---------------- #
    async def scan_and_analyze(self):
        print(f"[{datetime.now()}] start cycle")
        await send_telegram_message("⏳ Старт цикла сканирования")

        try:
            scan_start = time.time()
            scan_result = await self.tracker.run_full_scan()
            projects = scan_result.get("projects") or []
            await send_telegram_message(f"📊 Источники просканированы за {time.time() - scan_start:.1f}s")

            if not projects:
                await send_telegram_message("⚠️ Новых проектов не найдено")
                return

            limit = self.scan_cfg.get("max_projects_per_scan", 20)
            total = min(limit, len(projects))
            delay_between = self.scan_cfg.get("delay_between", 1)

            for idx, project in enumerate(projects[:limit], 1):
                await send_telegram_message(f"🔎 Анализ {idx}/{total}: {project.get('name')}")
                try:
                    analysis = await self.analyzer.analyze_project(project)
                    strategy = self.strategy_gen.generate_strategy(project, analysis.get("score", 0))
                    analysis["strategy"] = strategy

                    await self.save_analysis(project["id"], analysis)

                    if await self.should_notify(analysis):
                        await self.send_notification(project, analysis)
                except Exception as e:
                    await self._notify_error(f"Ошибка анализа {project.get('name')}: {e}")
                await asyncio.sleep(delay_between)

            await self._notify_scan_complete()
        except Exception as e:
            print(f"Error in cycle: {e}")
            await self._notify_error(str(e))

    async def run_scheduled(self):
        """Асинхронный планировщик без вложенных asyncio.run."""
        interval = max(int(self.scan_cfg.get("interval", 1800)), 60)
        while True:
            await self.scan_and_analyze()
            await asyncio.sleep(interval)

    def stop(self):
        self.running = False

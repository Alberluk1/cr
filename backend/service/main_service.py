import asyncio
import json
import sqlite3
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

import schedule

from backend.config import get_notifications_config, get_scanner_config, get_db_path
from backend.scanner.crypto_scanner import CryptoTracker
from backend.analyzer.crypto_analyzer import CryptoAnalyzer
from backend.telegram_client import send_message as send_telegram_message
from backend.bot.telegram_logger import log_detailed
from backend.model_checker import check_models


class CryptoAlphaService:
    """Сервис автоматического сканирования и анализа."""

    def __init__(self):
        self.tracker = CryptoTracker()
        self.analyzer = CryptoAnalyzer()
        self.notifications_cfg = get_notifications_config()
        self.scan_cfg = get_scanner_config()
        self.running = False

    def _open_db(self):
        return sqlite3.connect(get_db_path())

    async def scan_and_analyze(self):
        """Полный цикл: скан -> анализ -> уведомление."""
        print(f"[{datetime.now()}] start cycle")
        await send_telegram_message("⏳ Старт цикла сканирования")
        await log_detailed("SCAN", "start_cycle")
        try:
            # Проверка моделей перед сканом
            model_info = await check_models()
            report_lines = ["🔍 Проверка моделей:", "✅ Доступно:"]
            report_lines += [f"• {m}" for m in model_info.get("available", [])]
            if model_info.get("missing"):
                report_lines.append("❌ Отсутствуют:")
                report_lines += [f"• {m}" for m in model_info.get("missing")]
            await send_telegram_message("\n".join(report_lines))

            scan_start = time.time()
            scan_result = await self.tracker.run_full_scan()
            source_counts = scan_result.get("source_counts", {})
            await log_detailed(
                "SCAN",
                "sources_completed",
                status=f"{time.time() - scan_start:.1f}s",
                details={"sources": source_counts},
            )
            await send_telegram_message(
                f"📊 Источники просканированы за {time.time() - scan_start:.1f}s"
            )

            projects = scan_result.get("projects") or await self.get_unanalyzed_projects()
            limit = self.scan_cfg.get("max_projects_per_scan", 20)
            for project in projects[:limit]:
                try:
                    await send_telegram_message(
                        f"🔎 Анализ: {project.get('name','Unknown')} ({project.get('source','unknown')})"
                    )
                    await log_detailed(
                        "ANALYZE",
                        "start",
                        data=project.get("name", "Unknown"),
                        details={"id": project.get("id"), "source": project.get("source")},
                    )
                    start = time.time()
                    analysis = await self.analyzer.analyze_project(project)
                    duration = time.time() - start
                    score_val = analysis.get("final_decision", {}).get("investment_analysis", {}).get("score_numeric", "N/A")
                    await log_detailed(
                        "ANALYZE",
                        "done",
                        data=project.get("name", "Unknown"),
                        status=f"{duration:.1f}s",
                        details={"score": score_val},
                    )
                    await send_telegram_message(
                        f"✅ Анализ завершен: {project.get('name','Unknown')} за {duration:.1f}s score={score_val}"
                    )
                    await self.save_analysis(project["id"], analysis)
                    await self._notify_project(project, analysis)
                    if await self.should_notify(analysis):
                        await self.send_notification(project, analysis)
                    await asyncio.sleep(5)  # Пауза для GPU
                except Exception as e:
                    await log_detailed(
                        "ANALYZE",
                        "error",
                        data=project.get("name", "Unknown"),
                        status=str(e),
                        details={"id": project.get("id")},
                        level="ERROR",
                    )
                    await self._notify_error(f"Ошибка анализа {project.get('id')}: {e}")
                    continue
        except Exception as e:
            print(f"Error in cycle: {e}")
            await self._notify_error(f"Ошибка в цикле: {e}")
        else:
            await self._notify_scan_complete()

    async def get_unanalyzed_projects(self) -> List[Dict[str, Any]]:
        """Проекты со статусом new."""
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
        projects: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            try:
                item["raw_data"] = json.loads(item.get("raw_data") or "{}")
            except Exception:
                item["raw_data"] = {}
            projects.append(item)
        conn.close()
        return projects

    async def save_analysis(self, project_id: str, analysis: Dict[str, Any]):
        """Сохраняет анализ и обновляет проект."""
        conn = self._open_db()
        cursor = conn.cursor()
        final = analysis.get("final_decision", {}) or {}
        inv = final.get("investment_analysis", final)
        score = inv.get("score_numeric", inv.get("final_score", 0))
        verdict = inv.get("recommendation", inv.get("verdict"))
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

    async def should_notify(self, analysis: Dict[str, Any]) -> bool:
        """Флаг: отправлять ли уведомление."""
        telegram_cfg = self.notifications_cfg.get("telegram", {})
        if not telegram_cfg.get("enabled", False):
            return False

        final = analysis.get("final_decision", {}) or {}
        inv = final.get("investment_analysis", final)
        score = inv.get("score_numeric", 0) or 0
        verdict = (inv.get("recommendation") or inv.get("verdict") or "").upper()
        threshold = telegram_cfg.get("alert_threshold", 8.0)

        if score >= threshold:
            return True
        if verdict in {"STRONG_BUY", "BUY", "SCAM"}:
            return True
        return False

    async def send_notification(self, project: Dict[str, Any], analysis: Dict[str, Any]):
        """Отправка уведомления (через Telegram при включении)."""
        try:
            from backend.bot.telegram_bot import CryptoAlertBot
        except ImportError:
            print("Telegram bot dependency missing.")
            return

        telegram_cfg = self.notifications_cfg.get("telegram", {})
        if not telegram_cfg.get("enabled", False):
            print("Telegram notifications disabled.")
            return

        bot = CryptoAlertBot(
            token=telegram_cfg.get("token", ""),
            chat_id=telegram_cfg.get("chat_id", ""),
        )
        await bot.send_alert(project, analysis)

    def _run_async(self, coro):
        asyncio.run(coro)

    def run_scheduled(self):
        """Запуск с расписанием."""
        # Стартовый прогон
        self._run_async(self.scan_and_analyze())

        interval = self.scan_cfg.get("interval", 1800)
        every = max(int(interval), 60)
        schedule.every(every).seconds.do(lambda: self._run_async(self.scan_and_analyze()))
        print(f"Scheduler: every {every} sec")

        self.running = True
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        self.running = False

    async def _notify_project(self, project: Dict[str, Any], analysis: Dict[str, Any]):
        """Отправка краткого уведомления о новом анализе (только high score)."""
        final = analysis.get("final_decision", {}) or {}
        inv = final.get("investment_analysis", final)
        score = inv.get("score_numeric", inv.get("final_score", 0)) or 0
        verdict = inv.get("recommendation", inv.get("verdict", "N/A"))
        if score < 8:
            return
        text = (
            "🚀 Высокий потенциал\n"
            f"*{project.get('name', 'Unknown')}* ({project.get('source', 'unknown')})\n"
            f"Оценка: *{score}/10* | Вердикт: *{verdict}*\n"
            f"Категория: {project.get('category', 'Unknown')}\n"
            f"ID: `{project.get('id')}`"
        )
        await send_telegram_message(text)

    async def _notify_scan_complete(self):
        """Краткое уведомление о завершении сканирования/анализа."""
        await send_telegram_message("✅ Сканирование завершено")

    async def _notify_error(self, message: str):
        """Отправка критической ошибки."""
        await send_telegram_message(f"⚠️ Ошибка: {message}")

    async def _notify_info(self, message: str):
        """Информационное уведомление."""
        await send_telegram_message(message)

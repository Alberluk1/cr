import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any

from telegram import Bot
from telegram.constants import ParseMode

from backend.config import get_db_path


class CryptoAlertBot:
    """Telegram бот для уведомлений."""

    def __init__(self, token: str, chat_id: str):
        self.bot = Bot(token=token)
        self.chat_id = chat_id
        self.db_path = get_db_path()

    async def send_alert(self, project: Dict[str, Any], analysis: Dict[str, Any]):
        final = analysis.get("final_decision", {}) or {}
        strengths = analysis.get("analyst_analysis", {}).get("strengths", [])
        risks = analysis.get("risk_analysis", {}).get("high_risks", [])

        message = f"""
🚨 *НОВЫЙ ПРОЕКТ* 🚨

*Название:* {project.get('name', 'Unknown')}
*Категория:* {project.get('category', 'Unknown')}
*Источник:* {project.get('source', 'Unknown')}

📊 *ОЦЕНКА:*
• Общий балл: *{final.get('final_score', 'N/A')}/10*
• Вердикт: *{final.get('verdict', 'N/A')}*
• Уверенность: {final.get('confidence', 'MEDIUM')}

📈 *Сильные стороны:*
{chr(10).join(f'• {s}' for s in strengths[:3])}

⚠️ *Риски:*
{chr(10).join(f'• {r}' for r in risks[:3])}

🕒 {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    async def send_daily_digest(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        start = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cursor.execute(
            """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN confidence_score >= 8 THEN 1 ELSE 0 END) as high_quality,
                   SUM(CASE WHEN confidence_score <= 3 THEN 1 ELSE 0 END) as scams
            FROM projects
            WHERE discovered_at >= ? AND status = 'analyzed'
            """,
            (start.isoformat(),),
        )
        stats = cursor.fetchone()
        message = f"""
📊 *ЕЖЕДНЕВНЫЙ ДАЙДЖЕСТ*

За последние 24 часа:
• Всего проектов: *{stats[0] or 0}*
• Высоко оцененных (8+): *{stats[1] or 0}*
• Потенциальных скамов: *{stats[2] or 0}*
"""
        cursor.execute(
            """
            SELECT name, confidence_score, verdict
            FROM projects
            WHERE discovered_at >= ? AND confidence_score >= 7
            ORDER BY confidence_score DESC
            LIMIT 5
            """,
            (start.isoformat(),),
        )
        rows = cursor.fetchall()
        for idx, (name, score, verdict) in enumerate(rows, 1):
            message += f"\n{idx}. *{name}* - {score}/10 ({verdict})"
        conn.close()
        await self.bot.send_message(
            chat_id=self.chat_id, text=message, parse_mode=ParseMode.MARKDOWN
        )

import logging
from typing import Any, Dict

from backend.telegram_client import send_message

logger = logging.getLogger(__name__)


class TelegramBot:
    """Простая обёртка для отправки форматированных сообщений в Telegram."""

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def format_project_message(self, project: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        name = project.get("name", "Unknown")
        category = project.get("category", "Unknown")
        tvl = project.get("metrics", {}).get("tvl", 0)
        url = project.get("url", "нет ссылки")

        score = analysis.get("score", 0)
        verdict = analysis.get("verdict", "UNKNOWN")
        summary = analysis.get("summary") or analysis.get("project_summary", "нет описания")
        risk_level = analysis.get("risk_level", analysis.get("main_risk", "неизвестно"))
        where_to_buy = analysis.get("where_to_buy", "неизвестно")
        growth = analysis.get("realistic_growth") or analysis.get("growth_potential") or "неизвестно"
        timeframe = analysis.get("growth_timeframe", "6-12 месяцев")

        message = f"""
🔍 *{name}*
📊 *Категория:* {category}
💰 *TVL:* ${tvl:,.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ *Оценка:* {score}/10
📈 *Вердикт:* {verdict}
🏆 *Потенциал:* {growth} (горизонт {timeframe})

💡 *Описание:*
{summary}

🏪 *Где купить:* {where_to_buy}
⚠️ *Риски:* {risk_level}

🔗 *Ссылка:* {url}
"""
        return message.strip()

    async def send_project_analysis(self, project: Dict[str, Any], analysis: Dict[str, Any]):
        """Форматирует и отправляет сообщение в Telegram."""
        message = self.format_project_message(project, analysis)
        await send_message(message, token=self.bot_token, chat_id=self.chat_id)
        logger.info("📤 Сообщение отправлено: %s", project.get("name"))

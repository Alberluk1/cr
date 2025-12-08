import logging
from typing import Any, Dict

from backend.telegram_client import send_message

logger = logging.getLogger(__name__)


class TelegramBot:
    """Простой обертка для отправки форматированных сообщений в Telegram."""

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
        quality = analysis.get("quality_assessment", analysis.get("team_assessment", "unknown"))
        growth = analysis.get("realistic_growth") or analysis.get("growth_potential") or "неизвестно"
        timeframe = analysis.get("growth_timeframe", "6-12 месяцев")

        strengths = analysis.get("key_strengths") or analysis.get("key_advantages") or []
        risks = analysis.get("main_risks") or analysis.get("key_risks") or []
        team = analysis.get("team_assessment", "неизвестно")
        product = analysis.get("product_status", analysis.get("product_readiness", "неизвестно"))

        inv = analysis.get("investment_recommendation", {}) or {}
        inv_size = inv.get("position_size") or inv.get("size") or "неизвестно"
        inv_entry = inv.get("entry_conditions") or inv.get("entry_strategy") or "неизвестно"
        exit_signals = inv.get("exit_signals") or analysis.get("exit_signals") or []

        message = f"""
🔍 *{name}*
📊 *Категория:* {category}
💰 *TVL:* ${tvl:,.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ *Оценка качества:* {score}/10
📈 *Вердикт:* {verdict}
🏆 *Качество:* {quality}

🎯 *Потенциал роста:* {growth}
⏱️ *Срок:* {timeframe}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ *Ключевые преимущества:*
"""
        for strength in strengths[:3]:
            message += f"• {strength}\n"

        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ *Основные риски:*\n"
        for risk in risks[:3]:
            message += f"• {risk}\n"

        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 *Команда:* {team}
🛠️ *Продукт:* {product}

💼 *Инвест. рекомендация:*
• Размер: {inv_size}
• Условия входа: {inv_entry}
"""
        if exit_signals:
            message += "• Сигналы выхода: " + "; ".join(exit_signals[:2]) + "\n"

        message += f"\n🔗 *Ссылка:* {url}\n"
        return message.strip()

    async def send_project_analysis(self, project: Dict[str, Any], analysis: Dict[str, Any]):
        """Форматирует и отправляет сообщение."""
        message = self.format_project_message(project, analysis)
        await send_message(message, token=self.bot_token, chat_id=self.chat_id)
        logger.info("📤 Сообщение отправлено: %s", project.get("name"))

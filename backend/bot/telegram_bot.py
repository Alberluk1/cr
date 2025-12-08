import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        # Заглушка: если нужно реальное отправление — подключите python-telegram-bot
        self.bot_token = bot_token
        self.chat_id = chat_id

    def format_project_message(self, project: Dict, analysis: Dict) -> str:
        """Новый формат для качественных проектов."""
        name = project.get("name", "Unknown")
        category = project.get("category", "Unknown")
        tvl = project.get("metrics", {}).get("tvl", 0)

        score = analysis.get("score", 0)
        verdict = analysis.get("verdict", "UNKNOWN")
        quality = analysis.get("quality_assessment", "unknown")
        growth = analysis.get("realistic_growth_potential") or analysis.get("realistic_growth", "n/a")
        timeframe = analysis.get("growth_timeframe") or analysis.get("timeframe", "6-12 месяцев")

        strengths = analysis.get("key_strengths") or analysis.get("key_advantages") or []
        risks = analysis.get("main_risks") or analysis.get("risks") or []
        team = analysis.get("team_assessment", "н/д")
        product = analysis.get("product_readiness", "н/д")

        inv = analysis.get("investment_recommendation", {}) or {}
        inv_size = inv.get("size", "н/д")
        inv_entry = inv.get("entry_strategy", "н/д")
        exit_signals = inv.get("exit_signals") or analysis.get("exit_signals") or []

        message = f"""
🔍 *{name}*
📊 *Категория:* {category}
💰 *TVL:* ${tvl:,.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ *ОЦЕНКА КАЧЕСТВА:* {score}/10
📈 *ВЕРДИКТ:* {verdict}
🏆 *КАЧЕСТВО:* {quality}

🎯 *ПОТЕНЦИАЛ РОСТА:* {growth}
⏱️ *СРОК:* {timeframe}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ *КЛЮЧЕВЫЕ ПРЕИМУЩЕСТВА:*
"""
        for strength in strengths[:3]:
            message += f"• {strength}\n"

        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ *ОСНОВНЫЕ РИСКИ:*\n"
        for risk in risks[:3]:
            message += f"• {risk}\n"

        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 *КОМАНДА:* {team}
🛠️ *ПРОДУКТ:* {product}

💼 *ИНВЕСТ. РЕКОМЕНДАЦИЯ:*
• Размер: {inv_size}
• Стратегия входа: {inv_entry}
"""
        if exit_signals:
            message += "• Выход: " + "; ".join(exit_signals[:2]) + "\n"

        message += f"\n🔗 *Ссылка:* {project.get('url', 'Нет')}\n"
        return message

    async def send_project_analysis(self, project: Dict, analysis: Dict):
        """Печать/лог (отправку можно прикрутить python-telegram-bot при наличии токена)."""
        try:
            message = self.format_project_message(project, analysis)
            print("\n" + "=" * 50)
            print(message)
            print("=" * 50 + "\n")
            logger.info(message)
        except Exception as e:
            logger.error(f"Ошибка форматирования сообщения: {e}")

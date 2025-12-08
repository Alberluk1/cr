import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        # Пока заглушка, можно подключить python-telegram-bot позже
        self.bot_token = bot_token
        self.chat_id = chat_id

    def format_project_message(self, project: Dict, analysis: Dict) -> str:
        """Форматирует ПОЛНОЕ сообщение о проекте"""

        score = analysis.get("score", 0)
        if score >= 8:
            header = "🚀 HIGH-POTENTIAL PROJECT 🚀"
        elif score >= 6:
            header = "📊 PROJECT ANALYSIS 📊"
        else:
            header = "⚠️ RISK WARNING ⚠️"

        name = project.get("name", "Unknown")
        category = project.get("category", "Unknown")
        source = project.get("source", "Unknown")

        links = project.get("links", {}) or {}
        links_text = ""
        for platform, url in links.items():
            if url and url.strip():
                links_text += f"• {platform.title()}: {url}\n"

        metrics = project.get("metrics", {}) or {}
        tvl = metrics.get("tvl", 0)
        tvl_change = metrics.get("tvl_change_7d", 0)
        chain = metrics.get("chain", "Unknown")

        verdict = analysis.get("verdict", "UNKNOWN")
        confidence = analysis.get("confidence", "MEDIUM")
        summary = analysis.get("summary", "No summary")
        strengths = analysis.get("strengths", []) or []
        weaknesses = analysis.get("weaknesses", []) or []
        strategy = analysis.get("strategy", "No strategy")
        models_used = analysis.get("models_used", 1)

        message = f"{header}\n\n"
        message += f"🏷️ *Название:* {name}\n"
        message += f"📊 *Категория:* {category} | 📍 {source}\n"
        message += f"⭐ *Оценка:* {score}/10 ({verdict})\n"
        message += f"🎯 *Уверенность:* {confidence}\n"
        message += f"🤖 *Моделей использовано:* {models_used}\n\n"

        message += f"🔗 *Основная ссылка:* {project.get('url', 'Нет ссылки')}\n\n"

        if links_text:
            message += "🌐 *Все ссылки:*\n"
            message += links_text + "\n"

        message += f"📈 *Метрики:*\n"
        message += f"• TVL: ${tvl:,.0f}\n"
        if tvl_change != 0:
            change_emoji = "📈" if tvl_change > 0 else "📉"
            message += f"• Изменение TVL (7д): {change_emoji} {tvl_change:+.1f}%\n"
        message += f"• Блокчейн: {chain}\n\n"

        message += f"💡 *Что это:*\n{summary}\n\n"

        if strengths:
            message += "✅ *Сильные стороны:*\n"
            for i, strength in enumerate(strengths[:3], 1):
                message += f"{i}. {strength}\n"
            message += "\n"

        if weaknesses:
            message += "⚠️ *Риски и слабые стороны:*\n"
            for i, weakness in enumerate(weaknesses[:3], 1):
                message += f"{i}. {weakness}\n"
            message += "\n"

        message += f"💰 *Стратегия инвестирования:*\n{strategy}\n\n"

        message += f"#{category.replace(' ', '')} #{source} "
        if score >= 8:
            message += "#HighPotential "
        elif score >= 6:
            message += "#MediumPotential "
        else:
            message += "#Risky "
        if "tvl" in metrics and metrics["tvl"] > 0:
            message += "#TVL "

        return message

    async def send_project_analysis(self, project: Dict, analysis: Dict):
        """Отправляет анализ в Telegram или лог."""
        try:
            message = self.format_project_message(project, analysis)

            # Здесь могла бы быть реальная отправка через python-telegram-bot
            # если token/chat_id заданы. Пока просто лог/консоль.
            logger.info("\n" + "=" * 50)
            logger.info(f"📤 ГОТОВО К ОТПРАВКЕ: {project.get('name')}")
            logger.info("\n" + message)
            logger.info("=" * 50 + "\n")

            print("\n" + "=" * 50)
            print(message)
            print("=" * 50 + "\n")

        except Exception as e:
            logger.error(f"❌ Ошибка форматирования сообщения: {e}")
            fallback = f"🔍 {project.get('name')}\n"
            fallback += f"⭐ Оценка: {analysis.get('score', 0)}/10\n"
            fallback += f"🔗 Ссылка: {project.get('url', 'Нет')}"
            print(fallback)

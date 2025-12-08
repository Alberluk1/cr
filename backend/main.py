import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from backend.analyzer.deepseek_analyzer import DeepSeekAnalyzer
from backend.scanner.crypto_scanner import CryptoTracker
from backend.telegram_client import send_message

# Настраиваем логирование (DEBUG для диагностики DeepSeek)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def format_message(project: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Формирует сообщение в расширенном формате для Telegram."""
    name = project.get("name", "Unknown")
    category = project.get("category", "Unknown")
    tvl = project.get("metrics", {}).get("tvl", 0)
    score = analysis.get("score", 0)
    verdict = analysis.get("verdict", "UNKNOWN")

    has_token = analysis.get("has_token")
    token_symbol = analysis.get("token_symbol", "неизвестно")
    where_to_buy = analysis.get("where_to_buy", "неизвестно")
    growth = analysis.get("realistic_growth", analysis.get("growth_potential", "неизвестно"))
    plan = analysis.get("concrete_plan", analysis.get("investment_recommendation", {}).get("how_to_invest", "нет плана"))
    main_risk = analysis.get("main_risk") or (analysis.get("key_risks") or ["неизвестно"])[0]

    msg = f"""
🔍 *{name}*
📊 *Категория:* {category}
💰 *TVL:* ${tvl:,.0f}
🔗 {project.get('url', 'Нет ссылки')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ *Оценка:* {score}/10
📈 *Вердикт:* {verdict}
📈 *Потенциал:* {growth}

💎 *Токен:* {"есть" if has_token else "нет"} ({token_symbol})
🏪 *Где купить:* {where_to_buy}

💡 *Описание:*
{analysis.get('project_summary', 'неизвестно')}

📋 *План действий:*
{plan}

⚠️ *Главный риск:* {main_risk}
🤖 *Анализ:* DeepSeek AI
"""
    return msg.strip()


async def main():
    logger.info("🚀 Crypto Scanner (DeepSeek)")

    scanner = CryptoTracker()
    analyzer = DeepSeekAnalyzer()

    # Сканирование
    scan_result = await scanner.run_full_scan()
    projects = scan_result.get("projects", [])
    if not projects:
        logger.warning("Проекты не найдены")
        return

    logger.info("📊 Найдено %s проектов для анализа", len(projects))

    for idx, project in enumerate(projects[:10], 1):
        logger.info("🔎 Анализ %s/%s: %s", idx, min(10, len(projects)), project.get("name"))
        analysis = await analyzer.analyze_project(project)
        message = format_message(project, analysis)
        await send_message(message)
        await asyncio.sleep(1)

    logger.info("✅ Анализ завершен")


if __name__ == "__main__":
    # Добавляем корень проекта в sys.path на всякий случай
    ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.append(str(ROOT_DIR))
    asyncio.run(main())

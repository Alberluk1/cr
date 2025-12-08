import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.scanner.crypto_scanner import CryptoTracker
from backend.analyzer.advanced_analyzer import AdvancedAnalyzer
from backend.ollama_client import OllamaClient
from backend.telegram_client import send_message

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


def format_message(project: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Формат сообщения для отправки в Telegram/лог."""
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

    msg = f"""
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
    for s in strengths[:3]:
        msg += f"• {s}\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ *ОСНОВНЫЕ РИСКИ:*\n"
    for r in risks[:3]:
        msg += f"• {r}\n"

    msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 *КОМАНДА:* {team}
🛠️ *ПРОДУКТ:* {product}

💼 *ИНВЕСТ. РЕКОМЕНДАЦИЯ:*
• Размер: {inv_size}
• Стратегия входа: {inv_entry}
"""
    if exit_signals:
        msg += "• Выход: " + "; ".join(exit_signals[:2]) + "\n"

    msg += f"\n🔗 *Ссылка:* {project.get('url', 'Нет ссылки')}\n"
    return msg.strip()


async def main():
    logger.info("🚀 Crypto Scanner стартует")

    scanner = CryptoTracker()
    ollama_client = OllamaClient()
    analyzer = AdvancedAnalyzer(ollama_client)

    scan_result = await scanner.run_full_scan()
    projects = scan_result if isinstance(scan_result, list) else scan_result.get("projects", [])

    if not projects:
        logger.warning("Проекты не найдены")
        return

    logger.info(f"📊 Найдено {len(projects)} проектов для анализа")

    # Анализируем до 10 проектов
    for idx, project in enumerate(projects[:10], 1):
        logger.info(f"🔎 Анализ {idx}/{min(10, len(projects))}: {project.get('name')}")
        analysis = await analyzer.analyze_project(project)

        message = format_message(project, analysis)
        # Отправка в Telegram
        await send_message(message)

        # Дополнительный лог качества/роста
        if analysis and "quality_assessment" in analysis:
            logger.info(
                f"✅ {project.get('name')}: качество {analysis.get('quality_assessment')}, "
                f"потенциал {analysis.get('realistic_growth_potential') or analysis.get('realistic_growth', 'n/a')}"
            )
        else:
            logger.warning(f"⚠️ Старый формат анализа для {project.get('name')}")

        # Небольшая пауза, чтобы не спамить GPU/LLM
        await asyncio.sleep(1)

    logger.info("✅ Анализ завершен")


if __name__ == "__main__":
    asyncio.run(main())

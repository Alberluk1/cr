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
from backend.analyzer.deepseek_analyzer import DeepSeekAnalyzer
from backend.telegram_client import send_message

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


def format_message(project: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Формат сообщения для DeepSeek-анализа."""
    name = project.get("name", "Unknown")
    category = project.get("category", "Unknown")
    tvl = project.get("metrics", {}).get("tvl", 0)
    score = analysis.get("score", 0)
    verdict = analysis.get("verdict", "UNKNOWN")

    inv = analysis.get("investment_recommendation", {}) or {}
    risks = analysis.get("key_risks") or []

    msg = f"""
🔍 *{name}*
📊 {category} | 💰 TVL: ${tvl:,.0f}
🔗 {project.get('url', 'Нет ссылки')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ ОЦЕНКА: {score}/10
📈 ВЕРДИКТ: {verdict}

💡 ЧТО ЭТО: {analysis.get('project_summary', 'н/д')}
👥 КОМАНДА: {analysis.get('team_assessment', 'н/д')}
🛠️ ПРОДУКТ: {analysis.get('product_status', 'н/д')}
📊 ПОТЕНЦИАЛ: {analysis.get('growth_potential', 'н/д')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ РЕКОМЕНДАЦИЯ: {"Инвестировать" if inv.get('should_invest') else "Не инвестировать"}

📋 ПЛАН ДЕЙСТВИЙ:
{inv.get('how_to_invest', 'Нет плана')}

💰 РАЗМЕР ПОЗИЦИИ: {inv.get('position_size', 'Не указан')}
🎯 УСЛОВИЯ ВХОДА: {inv.get('entry_conditions', 'Не указаны')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ КЛЮЧЕВЫЕ РИСКИ:
"""
    for risk in risks[:3]:
        msg += f"• {risk}\n"

    if analysis.get("critical_events"):
        msg += f"\n🚨 КРИТИЧЕСКИЕ СОБЫТИЯ:\n{analysis['critical_events']}\n"

    msg += f"\n🤖 АНАЛИЗ: DeepSeek AI\n"
    return msg.strip()


async def main():
    logger.info("🚀 Crypto Scanner стартует")

    scanner = CryptoTracker()
    analyzer = DeepSeekAnalyzer()

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
        await send_message(message)

        # Небольшая пауза
        await asyncio.sleep(1)

    logger.info("✅ Анализ завершен")


if __name__ == "__main__":
    asyncio.run(main())

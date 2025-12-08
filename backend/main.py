import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.analyzer.openrouter_analyzer import EnsembleOpenRouterAnalyzer
from backend.scanner.crypto_scanner import CryptoTracker
from backend.telegram_client import send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def format_message(project: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    name = project.get("name", "Unknown")
    category = project.get("category", "Unknown")
    tvl = project.get("metrics", {}).get("tvl", 0)
    score = analysis.get("score", 0)
    verdict = analysis.get("verdict", "UNKNOWN")

    token_symbol = analysis.get("token_symbol", "unknown")
    where_to_buy = analysis.get("where_to_buy", "unknown")
    exchanges = analysis.get("exchanges") or []
    buy_links = analysis.get("buy_links") or []
    contract = analysis.get("contract_address", "unknown")
    growth = analysis.get("realistic_growth", analysis.get("growth_potential", "unknown"))
    plan = analysis.get("plan", "No plan provided")
    main_risk = analysis.get("main_risk", "unknown")

    msg = f"""
🔍 *{name}*
📊 *Category:* {category}
💰 *TVL:* ${tvl:,.0f}
🔗 {project.get('url', 'no link')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ *Score:* {score}/10
📈 *Verdict:* {verdict}
🏆 *Growth:* {growth}

💎 *Token:* {token_symbol}
🛒 *Where to buy:* {where_to_buy}
🏦 *Exchanges:* {', '.join(exchanges) if exchanges else 'unknown'}
🔗 *Links:* {', '.join(buy_links) if buy_links else 'unknown'}
📝 *Contract:* {contract}

💡 *Summary:*
{analysis.get('summary', 'No summary')}

📝 *Plan:*
{plan}

⚠️ *Main risk:* {main_risk}
🤖 *Model:* OpenRouter
"""
    return msg.strip()


async def main():
    logger.info("🚀 Crypto Scanner (OpenRouter)")

    scanner = CryptoTracker()
    try:
        analyzer = EnsembleOpenRouterAnalyzer()
    except Exception as e:
        logger.error("OPENROUTER_API_KEY is not set or invalid: %s", e)
        await send_message("⚠️ OPENROUTER_API_KEY not configured.")
        return

    scan_result = await scanner.run_full_scan()
    projects = scan_result.get("projects", [])
    if not projects:
        logger.warning("No projects found.")
        return

    logger.info("Found %s projects to analyze.", len(projects))

    # limit to 1 project per run to save free-model daily quota
    for idx, project in enumerate(projects[:1], 1):
        logger.info("Analyzing %s/%s: %s", idx, min(1, len(projects)), project.get("name"))
        analysis = await analyzer.analyze_project(project)
        message = format_message(project, analysis)
        await send_message(message)
        await asyncio.sleep(1)

    logger.info("Analysis complete.")


if __name__ == "__main__":
    asyncio.run(main())
    contract = analysis.get("contract_address", "unknown")

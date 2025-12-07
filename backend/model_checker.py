import asyncio
from typing import List, Dict, Any

import aiohttp

from backend.bot.telegram_logger import log_detailed
from backend.config import get_llm_models


async def fetch_available_models(base_url: str) -> List[str]:
    """Запрашивает список моделей из Ollama."""
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [m.get("name") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


async def check_models() -> Dict[str, Any]:
    """Проверка наличия моделей Ollama vs конфиг."""
    cfg = get_llm_models()
    base_url = cfg.get("base_url", "http://localhost:11434")
    required = cfg.get("council", []) + ([cfg.get("chairman")] if cfg.get("chairman") else [])
    required = [m for m in required if m]
    available = await fetch_available_models(base_url)

    missing = [m for m in required if m not in available]
    return {
        "base_url": base_url,
        "required": required,
        "available": available,
        "missing": missing,
    }


async def report_models():
    """Отчет в Telegram о доступности моделей."""
    info = await check_models()
    lines = ["🔍 [MODEL CHECK]", "════════════════════════════"]
    if info["available"]:
        lines.append("✅ ДОСТУПНЫЕ:")
        lines.extend(f"• {m}" for m in info["available"])
    if info["missing"]:
        lines.append("\n❌ ОТСУТСТВУЮЩИЕ:")
        lines.extend(f"• {m}" for m in info["missing"])
        lines.append("\n💡 РЕШЕНИЕ:")
        lines.extend(f"ollama pull {m}" for m in info["missing"])
    text_report = "\n".join(lines)
    await log_detailed(
        "OLLAMA",
        "model_check",
        data="; ".join(info["available"]),
        status=f"missing={len(info['missing'])}",
        details={"missing": ", ".join(info["missing"]) if info["missing"] else "none"},
    )
    return text_report

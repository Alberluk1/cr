import asyncio
import json
import psutil
import aiohttp
from typing import Dict, Any

from backend.bot.telegram_logger import log_detailed
from backend.model_checker import check_models


class SystemMonitor:
    @staticmethod
    async def check_ollama_health() -> Dict[str, Any]:
        """Проверяет доступность Ollama и моделей."""
        result = {"ollama": "down", "models": {}}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags", timeout=5) as resp:
                    result["ollama"] = resp.status
                    if resp.status == 200:
                        data = await resp.json()
                        result["models"] = {m.get("name"): m.get("modified_at") for m in data.get("models", [])}
        except Exception as e:
            result["error"] = str(e)
        return result

    @staticmethod
    async def check_llm_response(model: str = "llama3.2:3b-instruct-q4_K_M") -> Dict[str, Any]:
        """Простой запрос к LLM."""
        payload = {
            "model": model,
            "prompt": 'Return only JSON: {"test": "ok"}',
            "stream": False,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:11434/api/generate", json=payload, timeout=30) as resp:
                    data = await resp.json()
                    return {"status": resp.status, "response": json.dumps(data)[:200]}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def report():
        """Отправляет краткий отчёт в Telegram."""
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        ollama = await SystemMonitor.check_ollama_health()
        models = await check_models()
        await log_detailed(
            "MONITOR",
            "system",
            status=f"CPU {cpu}%, MEM {mem}%",
            details={"ollama": ollama, "models_missing": models.get("missing", [])},
        )

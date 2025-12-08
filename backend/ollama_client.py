import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import aiohttp
import httpx

from backend.bot.telegram_logger import log_detailed


class OllamaClient:
    """
    Небольшой async‑клиент для Ollama.
    Совместим с интерфейсом AsyncClient.chat (возвращает {"message": {"content": ...}}).
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    @asynccontextmanager
    async def session(self):
        """Контекстный менеджер для повторного использования aiohttp-сессии."""
        self._session = aiohttp.ClientSession()
        try:
            yield self
        finally:
            if self._session:
                await self._session.close()
                self._session = None

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        num_predict: int = 2048,
        top_p: float = 0.9,
        timeout: int = 120,
        **kwargs: Any,
    ) -> str:
        """
        Вызов /api/chat без стриминга.
        Принимает произвольные **kwargs (например options) для совместимости с AsyncClient.
        """
        if not self._session:
            self._session = aiohttp.ClientSession()

        extra_options = kwargs.pop("options", {}) or {}
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "top_p": top_p,
                **extra_options,
            },
        }
        payload.update({k: v for k, v in kwargs.items() if k not in {"options"}})

        start = time.time()
        try:
            async with self._session.post(
                f"{self.base_url}/api/chat", json=payload, timeout=timeout
            ) as response:
                elapsed = time.time() - start
                if response.status == 200:
                    data = await response.json()
                    await log_detailed(
                        "OLLAMA",
                        "chat_completion",
                        data=f"model={model}",
                        status=f"{response.status} ({elapsed:.1f}s)",
                    )
                    return data.get("message", {}).get("content", "")
                text = await response.text()
                await log_detailed(
                    "OLLAMA",
                    "chat_completion_error",
                    data=f"model={model}",
                    status=f"{response.status} ({elapsed:.1f}s)",
                    details={"error": text},
                    level="ERROR",
                )
                return f"Error: {response.status} - {text}"
        except Exception as e:
            elapsed = time.time() - start
            await log_detailed(
                "OLLAMA",
                "chat_completion_exception",
                data=f"model={model}",
                status=f"fail ({elapsed:.1f}s)",
                details={"error": str(e)},
                level="ERROR",
            )
            return f"Exception: {str(e)}"

    async def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout: int = 30,
        **kwargs: Any,
    ) -> str:
        """Упрощенный вызов generate → chat_completion."""
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            return await asyncio.wait_for(
                self.chat_completion(model=model, messages=messages, **kwargs),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            return '{"error": "timeout", "message": "LLM timeout"}'
        except Exception as e:
            return json.dumps({"error": str(e), "message": "LLM error"})

    async def chat(self, model: str, messages: List[Dict[str, str]], **options: Any) -> Dict[str, Any]:
        """
        Совместимый с ollama.AsyncClient.chat: возвращает dict c message.content.
        """
        content = await self.chat_completion(model=model, messages=messages, **options)
        return {"message": {"content": content}}

    def list(self) -> Dict[str, Any]:
        """
        Синхронно возвращает список моделей через /api/tags.
        """
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = [{"name": m.get("name", "")} for m in data.get("models", [])]
                return {"models": models}
        except Exception:
            pass
        return {"models": []}

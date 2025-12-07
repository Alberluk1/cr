import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager
import time

from backend.bot.telegram_logger import log_detailed


class OllamaClient:
    """Простой клиент для Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    @asynccontextmanager
    async def session(self):
        """Контекстный менеджер для сессии."""
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
    ) -> str:
        """Асинхронный запрос к Ollama API."""
        if not self._session:
            self._session = aiohttp.ClientSession()

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "top_p": top_p,
            },
        }
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
        """Генерация с таймаутом и безопасным возвратом ошибки."""
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

import asyncio
import json
import logging
import os
import re
from typing import Any, Dict

from openai import OpenAI

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """
Ты — институциональный крипто-инвестор. Дай конкретный, реалистичный анализ проекта.
Всегда отвечай ТОЛЬКО JSON в формате ниже, без лишнего текста.

ДАННЫЕ ПРОЕКТА
- Название: {name}
- Категория: {category}
- TVL: ${tvl:,.0f}
- Описание: {description}
- Токен: {token_symbol}

ПРАВИЛА
- Не используй шаблонные фразы и пустые советы.
- Реалистичный потенциал по TVL:
  * <50k  -> 1-2x
  * 50k-200k -> 2-3x
  * 200k-500k -> 3-5x
  * >500k -> 3-5x максимум
- Один главный риск, один конкретный план действий.
- Если токена нет — напиши, что это сервис, инвестировать можно только через использование.
- Если не знаешь — пиши "неизвестно".

ФОРМАТ ОТВЕТА (ТОЛЬКО JSON):
{{
  "score": 1-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "summary": "краткое описание проекта",
  "where_to_buy": "dex/cex/нельзя купить",
  "realistic_growth": "1-2x/2-3x/3-5x",
  "main_risk": "один риск",
  "plan": "конкретные шаги инвестору"
}}
"""


class OpenRouterAnalyzer:
    """
    Анализатор, использующий OpenRouter (OpenAI совместимый API).
    Требует переменную окружения OPENROUTER_API_KEY.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        key = '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'
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY не задан")

        self.client = OpenAI(
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
        )
        # бесплатные/дешевые модели; можно переключить на другую
        self.model = model or "mistralai/mistral-7b-instruct:free"

    def _build_prompt(self, project: Dict[str, Any]) -> str:
        return PROMPT_TEMPLATE.format(
            name=project.get("name", "Unknown"),
            category=project.get("category", "Unknown"),
            tvl=project.get("metrics", {}).get("tvl", 0),
            description=project.get("description", ""),
            token_symbol=project.get("token_symbol") or "нет",
        )

    async def analyze_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(project)
        loop = asyncio.get_event_loop()

        try:
            completion = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Ты профессиональный крипто-аналитик."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=512,
                    temperature=0.4,
                ),
            )
            text = completion.choices[0].message.content
            logger.debug("Ответ OpenRouter: %s", text[:500])
            return self._parse_json(text)
        except Exception as e:
            logger.error("Ошибка OpenRouter анализа: %s", e, exc_info=True)
            return self._fallback(project)

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise ValueError("JSON block not found")
            data = json.loads(match.group())
            score = float(data.get("score", 5.0))
            data["score"] = max(1, min(10, score))
            data["verdict"] = str(data.get("verdict", "HOLD")).upper()
            return data
        except Exception as e:
            logger.warning("Не удалось распарсить JSON: %s", e)
            return self._fallback()

    def _fallback(self, project: Dict[str, Any] | None = None) -> Dict[str, Any]:
        tvl = (project or {}).get("metrics", {}).get("tvl", 0)
        if tvl > 500_000:
            score = 7.0
        elif tvl > 100_000:
            score = 6.0
        else:
            score = 5.0
        return {
            "score": score,
            "verdict": "HOLD",
            "summary": "Недостаточно данных для анализа",
            "where_to_buy": "неизвестно",
            "realistic_growth": "1-2x",
            "main_risk": "неизвестно",
            "plan": "требуется ручная проверка",
        }

import asyncio
import json
import logging
import os
import re
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class DeepSeekAnalyzer:
    """
    Анализатор, использующий DeepSeek API вместо локальных моделей.
    """

    def __init__(self, api_key: str | None = None):
        # Используем тестовый ключ по умолчанию, если не задан в окружении
        default_key = "sk-e5d551bb7e9642849f7ff975327e5556"
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or default_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

    # -------------------- Public API -------------------- #
    async def analyze_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполняет анализ проекта через DeepSeek API с подробным логированием.
        Всегда старается вернуть валидный словарь с ключевыми полями.
        """
        logger.info("🔍 Начинаю анализ проекта: %s", project.get("name"))

        prompt = self._create_analysis_prompt(project)
        logger.debug("📝 Промпт (%s символов)", len(prompt))

        try:
            response_text = await self._call_deepseek_api(prompt)
            logger.info("✅ Ответ DeepSeek получен (%s символов)", len(response_text))
            logger.debug("📄 Ответ DeepSeek: %s", response_text[:1000])

            analysis = self._parse_response(response_text)
            logger.info("🎯 Оценка проекта %s: %s", project.get("name"), analysis.get("score", "N/A"))
            return analysis
        except Exception as exc:
            logger.error("❌ Критическая ошибка анализа %s: %s", project.get("name"), exc, exc_info=True)
            return self._fallback_analysis(project)

    # -------------------- Prompt construction -------------------- #
    def _create_analysis_prompt(self, project: Dict[str, Any]) -> str:
        name = project.get("name", "Unknown")
        category = project.get("category", "Unknown")
        tvl = project.get("metrics", {}).get("tvl", 0)
        description = project.get("description", "")
        token_symbol = project.get("token_symbol") or "нет"

        prompt = f"""
ТЫ — ИНСТИТУЦИОНАЛЬНЫЙ КРИПТО-АНАЛИТИК. ДАЙ РЕАЛЬНО ПОЛЕЗНЫЙ АНАЛИЗ С КОНКРЕТНЫМИ ДЕЙСТВИЯМИ.

ДАННЫЕ ПРОЕКТА
• Название: {name}
• Категория: {category}
• TVL: ${tvl:,.0f}
• Описание: {description}
• Токен: {token_symbol}

ЖЕСТКИЕ ПРАВИЛА
1) НЕ используй шаблонные фразы вроде "постепенный вход" или "избегать пиков".
2) НЕ ставь потенциал >3x для TVL < $100k, >5x никогда не ставь.
3) Если нет токена — напиши, что это сервис, инвестировать можно только через использование.
4) Реалистичный потенциал считаем по формуле:
   • TVL < $50k  -> 1-2x
   • $50k-$200k  -> 2-3x
   • $200k-$500k -> 3-5x
5) Если ссылок или токена нет — пиши “НЕИЗВЕСТНО”, не выдумывай.
6) Укажи один главный риск, конкретный.
7) Дай четкий план: где купить, когда входить, стоп-лосс/выход.

ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON:
{{
  "has_token": true/false,
  "token_symbol": "XXX" или "нет",
  "where_to_buy": "Uniswap/Binance/нельзя купить",
  "current_price": "примерно $X" или "неизвестно",
  "market_cap": "примерно $Y" или "неизвестно",
  "is_service": true/false,
  "realistic_growth": "1-2x/2-3x/3-5x",
  "concrete_plan": "конкретные шаги инвестору",
  "main_risk": "один главный риск",
  "project_summary": "что за проект",
  "team_assessment": "опытная/анонимная/слабая/неизвестно",
  "product_status": "работает/бета/идея",
  "score": 1-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM"
}}

БУДЬ КРИТИЧНЫМ И РЕАЛИСТИЧНЫМ. ЕСЛИ НЕ ЗНАЕШЬ — ПИШИ 'НЕИЗВЕСТНО'.
"""
        return prompt

    # -------------------- DeepSeek API call -------------------- #
    async def _call_deepseek_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Ты профессиональный крипто-аналитик."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
        }

        logger.info("📤 Отправляю запрос в DeepSeek...")
        logger.debug("Запрос data: %s", json.dumps(payload, ensure_ascii=False)[:500])

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: requests.post(self.base_url, json=payload, headers=headers, timeout=30)
        )

        logger.info("📥 Ответ DeepSeek: %s", response.status_code)
        logger.debug("Ответ headers: %s", dict(response.headers))
        logger.debug("Ответ текст (первые 500): %s", response.text[:500])

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        if response.status_code == 401:
            raise RuntimeError("DeepSeek: неверный API ключ")
        if response.status_code == 429:
            raise RuntimeError("DeepSeek: превышен лимит запросов")
        raise RuntimeError(f"DeepSeek API error {response.status_code}: {response.text}")

    # -------------------- Parsing helpers -------------------- #
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        try:
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not match:
                raise ValueError("JSON block not found")
            analysis = json.loads(match.group())
            # Базовая валидация
            score = float(analysis.get("score", 5.0))
            analysis["score"] = max(1, min(10, score))
            verdict = str(analysis.get("verdict", "HOLD")).upper()
            analysis["verdict"] = verdict
            return analysis
        except Exception as exc:
            logger.warning("Ошибка парсинга ответа DeepSeek: %s", exc, exc_info=True)
            return self._fallback_analysis()

    # -------------------- Fallback -------------------- #
    def _fallback_analysis(self, project: Dict[str, Any] | None = None) -> Dict[str, Any]:
        tvl = (project or {}).get("metrics", {}).get("tvl", 0) if project else 0
        if tvl > 500_000:
            score = 7.0
        elif tvl > 100_000:
            score = 6.0
        else:
            score = 5.0
        return {
            "score": score,
            "verdict": "HOLD",
            "project_summary": "Недостаточно данных для анализа",
            "team_assessment": "неизвестно",
            "product_status": "неизвестно",
            "growth_potential": "1-2x",
            "investment_recommendation": {
                "should_invest": False,
                "how_to_invest": "Требуется дополнительный анализ",
                "position_size": "$0",
                "entry_conditions": "Не входить",
                "exit_signals": [],
            },
            "key_risks": ["Недостаточно данных"],
            "critical_events": "Неизвестно",
        }

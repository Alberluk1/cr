import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """
Ты DeFi-инвестор с 5+ лет опыта. Верни ТОЛЬКО валидный JSON, без текста вне JSON.

Данные:
- Название: {name}
- Категория: {category}
- TVL (USD): {tvl:,.0f}
- Описание: {description}
- Токен (если известен): {token_symbol}

Правила:
- Если нет торгуемого токена, has_token=false, token_symbol="unknown", exchanges=[] и buy_links=[].
- Найди контрактный адрес токена (если он есть); если неизвестен — пиши "unknown".
- Генерируй ПРЯМЫЕ ссылки на пары (если есть контракт):
  * Uniswap: https://app.uniswap.org/swap?inputCurrency=ETH&outputCurrency=CONTRACT_ADDRESS
  * PancakeSwap: https://pancakeswap.finance/swap?inputCurrency=BNB&outputCurrency=CONTRACT_ADDRESS
  * 1inch: https://app.1inch.io/#/1/swap/ETH/CONTRACT_ADDRESS
- Система оценки (старт 6.0/10):
  * TVL > $100M: +2; TVL < $1M: -2
  * Низкая ликвидность: -2
  * Высокая конкуренция: -1
  * Команда известная: +1
  * Проект новый (<6 мес): -1
  * Если риски высокие — финальная оценка не выше 5.0
- Реалистичный потенциал по TVL:
  * <50k  -> 1-2x
  * 50k-200k -> 2-3x
  * 200k-500k -> 3-5x
  * >500k -> 3-5x (не выше)
- План действий: чёткие шаги (вход/докупка/стоп/цели).
- Если данных нет — пиши "unknown", не выдумывай.

Верни JSON строго такого вида:
{{
  "score": 1-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "summary": "кратко что это за проект (по-русски)",
  "has_token": true/false,
  "token_symbol": "XXX или unknown",
  "contract_address": "0x... или unknown",
  "exchanges": ["Binance", "Uniswap"] или [],
  "buy_links": ["https://..."] или [],
  "where_to_buy": "dex/cex/ido/unknown",
  "realistic_growth": "1-2x/2-3x/3-5x",
  "main_risk": "один главный риск",
  "plan": "конкретный следующий шаг для инвестора (по-русски)"
}}
"""


class OpenRouterAnalyzer:
    """
    Lightweight analyzer that calls OpenRouter (OpenAI-compatible API).
    Requires env OPENROUTER_API_KEY.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")

        # Optional, helps OpenRouter identify the app
        default_headers = {
            "HTTP-Referer": "http://localhost",
            "X-Title": "Crypto Alpha Scout",
        }

        self.client = OpenAI(
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
            default_headers=default_headers,
        )
        self.model = model or "mistralai/mistral-7b-instruct:free"

    def _build_prompt(self, project: Dict[str, Any]) -> str:
        return PROMPT_TEMPLATE.format(
            name=project.get("name", "Unknown"),
            category=project.get("category", "Unknown"),
            tvl=project.get("metrics", {}).get("tvl", 0) or 0,
            description=project.get("description", "") or "",
            token_symbol=project.get("token_symbol") or "unknown",
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
                        {"role": "system", "content": "Return only strict JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=500,
                    temperature=0.35,
                ),
            )
            text = completion.choices[0].message.content
            logger.debug("OpenRouter raw response: %s", text[:500])
            return self._parse_json(text)
        except Exception as e:
            logger.error("OpenRouter analysis error: %s", e, exc_info=True)
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
            data.setdefault("has_token", False)
            data.setdefault("token_symbol", "unknown")
            data.setdefault("contract_address", "unknown")
            data.setdefault("where_to_buy", "unknown")
            data.setdefault("exchanges", [])
            data.setdefault("buy_links", [])
            data.setdefault("realistic_growth", "1-2x")
            data.setdefault("main_risk", "unknown")
            data.setdefault("plan", "collect more data")
            data.setdefault("summary", "No summary")
            return data
        except Exception as e:
            logger.warning("Cannot parse JSON from OpenRouter: %s", e)
            return self._fallback()

    def _fallback(self, project: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        tvl = (project or {}).get("metrics", {}).get("tvl", 0) or 0
        if tvl > 500_000:
            score = 7.0
        elif tvl > 100_000:
            score = 6.0
        else:
            score = 5.0
        return {
            "score": score,
            "verdict": "HOLD",
            "summary": "Fallback analysis; LLM unavailable",
            "has_token": False,
            "token_symbol": "unknown",
            "contract_address": "unknown",
            "where_to_buy": "unknown",
            "exchanges": [],
            "buy_links": [],
            "realistic_growth": "1-2x",
            "main_risk": "insufficient data",
            "plan": "await LLM result",
        }

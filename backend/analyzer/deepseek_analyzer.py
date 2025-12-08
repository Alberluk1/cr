import asyncio
import json
import logging
import os
import re
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class DeepSeekAnalyzer:
    """Анализ проектов через DeepSeek API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY не задан. Анализ будет возвращать fallback.")

    async def analyze_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            return self._get_fallback_analysis(project)
        try:
            prompt = self._create_analysis_prompt(project)
            response_text = await self._call_deepseek_api(prompt)
            analysis = self._parse_response(response_text)
            logger.info(f"✅ DeepSeek анализ {project.get('name')}: {analysis.get('score', 'N/A')}/10")
            return analysis
        except Exception as e:
            logger.error(f"❌ Ошибка DeepSeek анализа: {e}")
            return self._get_fallback_analysis(project)

    def _create_analysis_prompt(self, project: Dict[str, Any]) -> str:
        name = project.get("name", "Unknown")
        url = project.get("url", "")
        tvl = project.get("metrics", {}).get("tvl", 0)
        category = project.get("category", "Unknown")
        return f"""
ТЫ - ПРОФЕССИОНАЛЬНЫЙ КРИПТО-АНАЛИТИК.
ПРОАНАЛИЗИРУЙ ПРОЕКТ И ДАЙ КОНКРЕТНЫЕ РЕКОМЕНДАЦИИ (БЕЗ ШАБЛОНОВ).

ДАННЫЕ:
Название: {name}
Ссылка: {url}
TVL: ${tvl:,.0f}
Категория: {category}

ПРОВЕРЬ:
• История: взломы/скандалы? негативные новости? изменение TVL?
• Команда/продукт: опыт, работает ли, преимущество?
• Риски: главный риск, конкуренты, регуляторы.

ОТВЕТЬ ТОЛЬКО JSON:
{{
  "score": 1-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "project_summary": "одно предложение что это",
  "team_assessment": "оценка команды",
  "product_status": "работает/в разработке/идея",
  "growth_potential": "1-2x/2-3x/3-5x (реалистично)",
  "investment_recommendation": {{
    "should_invest": true/false,
    "how_to_invest": "конкретный план действий",
    "position_size": "$XXX - $XXX",
    "entry_conditions": "когда входить",
    "exit_signals": ["сигнал1", "сигнал2"]
  }},
  "key_risks": ["риск1", "риск2", "риск3"],
  "critical_events": "взломы/скандалы/важные события"
}}
ЕСЛИ НЕ ЗНАЕШЬ — ПИШИ \"НЕИЗВЕСТНО\".
"""

    async def _call_deepseek_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Ты профессиональный крипто-аналитик."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
        }
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: requests.post(self.base_url, json=data, headers=headers, timeout=30)
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        try:
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                analysis = json.loads(match.group())
                if "score" in analysis:
                    score = float(analysis["score"])
                    analysis["score"] = max(1, min(10, score))
                return analysis
        except Exception as e:
            logger.warning(f"Ошибка парсинга JSON: {e}")
        return self._get_fallback_analysis()

    def _get_fallback_analysis(self, project: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return {
            "score": 5.0,
            "verdict": "HOLD",
            "project_summary": "Не удалось проанализировать",
            "team_assessment": "Неизвестно",
            "product_status": "Неизвестно",
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

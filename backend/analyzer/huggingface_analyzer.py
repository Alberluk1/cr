import asyncio
import json
import logging
import re
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class HuggingFaceAnalyzer:
    """Простой анализатор через Hugging Face Inference API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("HF_API_KEY")
        if not self.api_key:
            raise RuntimeError("HF_API_KEY is not set; cannot call Hugging Face Inference API.")
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        # Используем TinyLlama через новый router endpoint для скорости
        self.model_url = "https://router.huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0"

    async def analyze_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = self._create_prompt(project)
            response_text = await self._call_api(prompt)
            analysis = self._parse_response(response_text)
            logger.info("✅ HuggingFace анализ %s: %s/10", project.get("name"), analysis.get("score", "N/A"))
            return analysis
        except Exception as e:
            logger.error("❌ Ошибка анализа: %s", e, exc_info=True)
            return self._fallback_analysis()

    def _create_prompt(self, project: Dict[str, Any]) -> str:
        return f"""<s>[INST]
Проанализируй крипто-проект:

Название: {project.get('name', 'Unknown')}
Ссылка: {project.get('url', '')}
TVL: ${project.get('metrics', {}).get('tvl', 0):,.0f}

Ответь в JSON формате:
{{
  "score": 1-10,
  "verdict": "BUY/HOLD/AVOID",
  "summary": "краткое описание",
  "risk_level": "низкий/средний/высокий"
}}
[/INST]"""

    async def _call_api(self, prompt: str) -> str:
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 300, "temperature": 0.3, "return_full_text": False},
        }
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: requests.post(self.model_url, headers=self.headers, json=payload, timeout=30)
        )
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "")
        raise Exception(f"API error: {response.status_code} - {response.text[:200]}")

    def _parse_response(self, text: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return self._fallback_analysis()

    def _fallback_analysis(self) -> Dict[str, Any]:
        return {"score": 5.0, "verdict": "HOLD", "summary": "Ошибка анализа", "risk_level": "неизвестно"}


async def test_analyzer():
    """Тест анализатора на одном проекте."""
    import os

    hf_key = os.getenv("HF_API_KEY") or ""
    if not hf_key:
        raise RuntimeError("HF_API_KEY is not set for test_analyzer.")
    analyzer = HuggingFaceAnalyzer(api_key=hf_key)
    test_project = {
        "name": "Euler Finance",
        "url": "https://www.euler.finance",
        "metrics": {"tvl": 62000},
    }
    print("🧪 Тестирую HuggingFaceAnalyzer...")
    res = await analyzer.analyze_project(test_project)
    print(res)


if __name__ == "__main__":
    asyncio.run(test_analyzer())

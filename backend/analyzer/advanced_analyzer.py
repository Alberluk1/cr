import json
import logging
import asyncio
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AdvancedAnalyzer:
    def __init__(self, ollama_client=None):
        if ollama_client is None:
            try:
                import ollama
                self.ollama = ollama.AsyncClient()
            except Exception as e:
                logger.error(f"Не удалось создать Ollama AsyncClient: {e}")
                self.ollama = None
        else:
            self.ollama = ollama_client

        self.available_models = self._get_available_models()
        self.analysis_cfg = {
            "analysis_timeout": 20,
            "delay_between": 1,
        }

    def _get_available_models(self) -> List[str]:
        try:
            if self.ollama and hasattr(self.ollama, "list"):
                models_response = self.ollama.list()
                installed_models = [m.get("name", "") for m in models_response.get("models", [])]
            else:
                installed_models = []
            possible = [
                "mistral",
                "llama3.2",
                "phi3",
                "qwen2.5",
                "gemma2",
            ]
            available: List[str] = []
            for base in possible:
                for inst in installed_models:
                    if inst.startswith(base):
                        available.append(inst)
                        break
            if not available:
                available = installed_models[:1] if installed_models else ["llama3.2:3b-instruct-q4_K_M"]
            logger.info(f"🎯 Используем модели: {available}")
            return available
        except Exception:
            return ["llama3.2:3b-instruct-q4_K_M"]

    def _create_prompt(self, project: Dict[str, Any]) -> str:
        name = project.get("name", "Unknown")
        desc = project.get("description", "No description")
        category = project.get("category", "Unknown")
        tvl = project.get("metrics", {}).get("tvl", 0)
        links = project.get("links", {}) or {}
        links_text = "\n".join(f"{k}: {v}" for k, v in links.items() if v)
        return f"""
Проанализируй крипто-проект:

Название: {name}
Описание: {desc}
Категория: {category}
TVL: ${tvl:,.0f}

Оцени от 1 до 10 и дай JSON ответ:
{{
  "score": число 1-10,
  "verdict": "BUY/HOLD/AVOID",
  "summary": "что это за проект",
  "confidence": "HIGH/MEDIUM/LOW"
}}
Только JSON.
Ссылки:
{links_text}
"""

    async def analyze_project(self, project: Dict) -> Dict[str, Any]:
        """Анализирует проект с помощью LLM."""
        logger.info(f"🔍 Анализ: {project.get('name')}")
        try:
            if not self.available_models or not self.ollama:
                return self._fallback(project)

            prompt = self._create_prompt(project)
            response = await self.ollama.chat(
                model=self.available_models[0],
                messages=[{"role": "user", "content": prompt}],
            )
            content = response["message"]["content"]
            logger.info(f"Ответ LLM: {content[:120]}...")
            analysis = json.loads(content)
            return analysis
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            return self._fallback(project)

    def _fallback(self, project: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "score": 5.0,
            "verdict": "HOLD",
            "summary": "Ошибка анализа",
            "confidence": "LOW",
        }

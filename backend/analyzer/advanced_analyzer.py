import json
import logging
import asyncio
import re
from typing import Dict, Any, List

from backend.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class AdvancedAnalyzer:
    def __init__(self, ollama_client=None):
        # ollama_client может быть не передан (совместимость с существующим кодом)
        self.ollama_client = ollama_client or OllamaClient()
        self.available_models = [
            "mistral:7b-instruct-q4KM",
            "qwen2.5:3b-instruct-q4KM",
            "phi3:mini",
            "gemma2:2b-instruct-q4KS",
            "llama3.2:3b-instruct-q4KM",
        ]
        # настройки анализа по умолчанию (используются в сервисе)
        self.analysis_cfg = {
            "analysis_timeout": 60,
            "delay_between": 2,
        }

    def _create_detailed_prompt(self, project: Dict) -> str:
        """Создает ДЕТАЛЬНЫЙ промпт с ВСЕМИ данными проекта"""
        name = project.get("name", "Unknown")
        description = project.get("description", "No description provided")
        category = project.get("category", "Unknown")
        url = project.get("url", "No URL")

        links = project.get("links", {}) or {}
        links_text = ""
        for platform, link in links.items():
            if link:
                links_text += f"{platform.upper()}: {link}\n"

        metrics = project.get("metrics", {}) or {}
        tvl = metrics.get("tvl", 0)
        tvl_change = metrics.get("tvl_change_7d", 0)
        chain = metrics.get("chain", "Unknown")
        audits = metrics.get("audits", 0)

        prompt = f"""
ТЫ: Эксперт по анализу крипто-проектов с 10-летним опытом.
ЗАДАЧА: Проанализировать проект и дать РАЗВЕРНУТЫЙ ответ.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ДАННЫЕ ПРОЕКТА:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ НАЗВАНИЕ: {name}
📊 КАТЕГОРИЯ: {category}
🔗 ОСНОВНАЯ ССЫЛКА: {url}

📝 ОПИСАНИЕ:
{description}

🔗 ВСЕ ССЫЛКИ:
{links_text}

📈 МЕТРИКИ:
• TVL (общая заблокированная стоимость): ${tvl:,.0f}
• Изменение TVL за 7 дней: {tvl_change:+.1f}%
• Блокчейн: {chain}
• Аудиты: {audits} {'✅' if audits > 0 else '❌'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 ТВОЙ АНАЛИЗ ДОЛЖЕН ВКЛЮЧАТЬ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ОЦЕНКА: от 1 до 10 (1=скам, 10=гем)
2. ВЕРДИКТ: STRONG_BUY / BUY / HOLD / AVOID / SCAM
3. УВЕРЕННОСТЬ: HIGH / MEDIUM / LOW
4. СУТЬ ПРОЕКТА: 1-2 предложения что это
5. СИЛЬНЫЕ СТОРОНЫ: 3-5 пунктов
6. СЛАБЫЕ СТОРОНЫ/РИСКИ: 3-5 пунктов
7. СТРАТЕГИЯ: что делать инвестору

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 ФОРМАТ ОТВЕТА (ТОЛЬКО JSON):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{
  "score": число от 1 до 10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "confidence": "HIGH/MEDIUM/LOW",
  "summary": "одно-два предложения что это за проект",
  "strengths": ["сильная сторона 1", "сильная сторона 2", "сильная сторона 3"],
  "weaknesses": ["риск 1", "риск 2", "риск 3"],
  "strategy": "конкретные действия для инвестора",
  "project_type": "DeFi/NFT/Gaming/Infrastructure/Other"
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❗ ВАЖНО: Будь КРИТИЧЕН и ОБЪЕКТИВЕН!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return prompt

    async def analyze_project(self, project: Dict) -> Dict[str, Any]:
        """Анализирует проект с КОНСЕНСУСОМ моделей"""
        logger.info(f"🔍 Анализ проекта: {project.get('name')}")

        try:
            prompt = self._create_detailed_prompt(project)

            tasks = []
            for model in self.available_models:
                tasks.append(self._analyze_with_model(model, prompt))

            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=15,
            )

            successful = [r for r in results if isinstance(r, dict) and "score" in r]
            if not successful:
                return self._get_fallback_analysis(project)

            scores = [a["score"] for a in successful if isinstance(a.get("score"), (int, float))]
            if not scores:
                return self._get_fallback_analysis(project)
            avg_score = sum(scores) / len(scores)

            best_analysis = min(successful, key=lambda x: abs(x["score"] - avg_score))
            best_analysis["score"] = round(avg_score, 1)
            best_analysis["models_used"] = len(successful)
            best_analysis["original_scores"] = scores
            return best_analysis

        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            return self._get_fallback_analysis(project)

    async def _analyze_with_model(self, model: str, prompt: str) -> Dict:
        """Анализ одной моделью"""
        try:
            async with self.ollama_client.session() as client:
                content = await client.generate(
                    model=model,
                    prompt=prompt,
                    temperature=0.2,
                    num_predict=500,
                    timeout=30,
                )

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                return {"score": 5.0, "error": "Invalid JSON"}

            analysis = json.loads(json_match.group())
            if "score" in analysis:
                score = float(analysis["score"])
                if 1 <= score <= 10:
                    return analysis
            return {"score": 5.0, "error": "Invalid score"}

        except Exception as e:
            return {"score": 5.0, "error": str(e)}

    def _get_fallback_analysis(self, project: Dict) -> Dict:
        """Анализ по умолчанию если все модели провалились"""
        return {
            "score": 5.0,
            "verdict": "HOLD",
            "confidence": "LOW",
            "summary": f"{project.get('name')} - {project.get('category', 'Unknown')} проект",
            "strengths": ["Новые данные отсутствуют"],
            "weaknesses": ["Не удалось проанализировать"],
            "strategy": "Требуется дополнительный анализ",
            "project_type": project.get("category", "Unknown"),
            "models_used": 0,
        }

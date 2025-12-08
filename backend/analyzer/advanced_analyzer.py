import asyncio
import json
import logging
import random
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class AdvancedAnalyzer:
    """
    Анализатор: опрашивает до 3 моделей Ollama, среднее по оценкам.
    Фокус на качестве проекта и реалистичном потенциале роста (1-5x, редко 5-8x).
    """

    def __init__(self, ollama_client=None):
        if ollama_client is None:
            try:
                from backend.ollama_client import OllamaClient
                self.ollama = OllamaClient()
            except Exception:
                self.ollama = None
        else:
            self.ollama = ollama_client

        self.available_models = self._get_available_models()
        self.analysis_cfg = {"analysis_timeout": 20, "delay_between": 1}

    def _get_available_models(self) -> List[str]:
        try:
            models: List[str] = []
            if self.ollama and hasattr(self.ollama, "list"):
                resp = self.ollama.list()
                raw_models = resp.get("models", []) if isinstance(resp, dict) else []
                for m in raw_models:
                    name = m.get("name")
                    if name:
                        models.append(name)
            priority = ["mistral", "llama3", "qwen", "phi", "gemma"]
            ordered: List[str] = []
            for p in priority:
                for m in models:
                    if m.startswith(p) and m not in ordered:
                        ordered.append(m)
            if not ordered:
                ordered = ["llama3.2:3b-instruct-q4_K_M"]
            logger.info(f"Используем модели: {ordered}")
            return ordered
        except Exception as e:
            logger.warning(f"Не удалось получить список моделей: {e}")
            return ["llama3.2:3b-instruct-q4_K_M"]

    def _create_detailed_prompt(self, project: Dict[str, Any]) -> str:
        name = project.get("name", "Unknown")
        category = project.get("category", "Unknown")
        tvl = project.get("metrics", {}).get("tvl", 0)
        description = project.get("description", "No description")
        return f"""
ТЫ - ИНСТИТУЦИОНАЛЬНЫЙ ИНВЕСТОР С ФОКУСОМ НА КАЧЕСТВО.
НУЖЕН ТОЧНЫЙ АНАЛИЗ БЕЗ ШАБЛОНОВ.

СТРОГИЕ ПРАВИЛА:
• Запрещены фразы типа "постепенный вход", "избегая пиков", "работающий продукт".
• НЕ ставь >3x при TVL < $100k. Потенциал строго по TVL:
  - TVL < $50k  → максимум 1-2x
  - $50k-$200k → максимум 2-3x
  - $200k-$500k → максимум 3-5x
  - >$500k     → максимум 5-8x (редко)
• Если нет токена — явно пиши: "ЭТО СЕРВИС, токена нет. Инвестировать можно только использованием сервиса."
• Если не знаешь — пиши "НЕИЗВЕСТНО".
• Дай конкретику: есть ли токен, где купить, когда входить, один главный риск.

ДАННЫЕ ПРОЕКТА:
Название: {name}
Категория: {category}
TVL: ${tvl:,.0f}
Описание: {description}

ОТВЕТЬ ТОЛЬКО НА ЭТИ ВОПРОСЫ:
1) Есть ли токен? (да/нет + символ)
2) Где купить (DEX/CEX/IDO) и примерная текущая цена и капа (если знаешь)
3) Как инвестировать конкретно (пошагово)
4) Реалистичный потенциал по TVL правилам выше
5) Главный риск (один конкретный)

ФОРМАТ ОТВЕТА ТОЛЬКО JSON:
{{
  "has_token": true/false,
  "token_symbol": "XXX" или "нет",
  "where_to_buy": "Uniswap/Binance/IDO/нельзя купить",
  "is_service": true/false,
  "realistic_growth_potential": "1-2x/2-3x/3-5x/5-8x",
  "concrete_plan": "Купить токен XXX на Y, затем ...",
  "main_risk": "один главный риск",
  "project_type": "Токен/NFT/Сервис",
  "score": 1-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID",
  "quality_assessment": "высокий/средний/низкий",
  "growth_timeframe": "6-12 месяцев",
  "investment_recommendation": {{
    "size": "$XXX - $XXX",
    "entry_strategy": "конкретное условие входа",
    "exit_signals": ["сигнал1", "сигнал2"]
  }},
  "key_strengths": ["сила1", "сила2", "сила3"],
  "main_risks": ["риск1", "риск2", "риск3"],
  "team_assessment": "опытная/анонимная/слабая",
  "product_readiness": "работает/бета/идея",
  "summary": "1-2 предложения что это"
}}
НЕ ИСПОЛЬЗУЙ ОБЩИЕ ФРАЗЫ. ЕСЛИ ДАННЫХ НЕТ — ПИШИ НЕИЗВЕСТНО.
"""

    async def analyze_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        if not self.available_models or not self.ollama:
            return self._enrich_strategy(self._smart_fallback(project), project)

        prompt = self._create_detailed_prompt(project)
        tasks = [self._analyze_with_model(m, prompt) for m in self.available_models[:3]]

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.analysis_cfg.get("analysis_timeout", 20),
            )
        except asyncio.TimeoutError:
            return self._enrich_strategy(self._smart_fallback(project), project)

        analyses: List[Dict[str, Any]] = []
        for res in results:
            if isinstance(res, dict) and "score" in res:
                analyses.append(res)

        if analyses:
            scores = [float(a.get("score", 5.0)) for a in analyses]
            avg = sum(scores) / len(scores) if scores else 5.0
            best = min(analyses, key=lambda a: abs(a.get("score", 5) - avg))
            best["score"] = round(avg, 1)
            best.setdefault("verdict", "HOLD")
            best.setdefault("summary", "Анализ выполнен")
            best.setdefault("confidence", "MEDIUM")
            best["models_used"] = len(analyses)
            return self._enrich_strategy(best, project)

        return self._enrich_strategy(self._smart_fallback(project), project)

    async def _analyze_with_model(self, model: str, prompt: str) -> Dict[str, Any]:
        try:
            response = await self.ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.7},
            )
            content = response.get("message", {}).get("content", "")
            parsed = self._extract_json(content)
            if "score" in parsed:
                logger.info(f"Ответ LLM ({model}): {parsed}")
                return parsed
        except Exception as e:
            logger.warning(f"Ошибка модели {model}: {e}")
        return {}

    def _extract_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            pass
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        num = re.search(r"\b([1-9]|10)\b", text)
        if num:
            score = float(num.group(1))
            verdict = "BUY" if score >= 7 else "HOLD" if score >= 5 else "AVOID"
            return {"score": score, "verdict": verdict, "summary": text[:120]}
        return {}

    def _smart_fallback(self, project: Dict[str, Any]) -> Dict[str, Any]:
        tvl = project.get("metrics", {}).get("tvl", 0)
        category = (project.get("category") or "").lower()
        if tvl > 500_000:
            base_score = 7.5
        elif tvl > 100_000:
            base_score = 6.5
        else:
            base_score = 5.5
        if "dex" in category:
            base_score += 0.3
        if "lending" in category:
            base_score += 0.2
        score = round(base_score + random.uniform(-0.5, 0.5), 1)
        score = max(1.0, min(10.0, score))
        verdict = "BUY" if score >= 7 else "HOLD" if score >= 5 else "AVOID"
        return {
            "score": score,
            "verdict": verdict,
            "summary": f"{project.get('name')} - {project.get('category', 'Unknown')}",
            "confidence": "MEDIUM",
            "models_used": 0,
        }

    def _enrich_strategy(self, analysis: Dict[str, Any], project: Dict[str, Any]) -> Dict[str, Any]:
        """Дополняем поля, если LLM их не выдал."""
        category = (project.get("category") or "").lower()
        tvl = project.get("metrics", {}).get("tvl", 0)

        def if_missing(key: str, value: Any):
            if key not in analysis or analysis.get(key) in (None, "", []):
                analysis[key] = value

        if not analysis:
            analysis = {}

        # growth band by score
        score_val = analysis.get("score", 6)
        if score_val >= 8:
            if_missing("realistic_growth_potential", "5-8x")
        elif score_val >= 7:
            if_missing("realistic_growth_potential", "3-5x")
        else:
            if_missing("realistic_growth_potential", "1-2x")
        if_missing("growth_timeframe", "6-12 месяцев")

        # strengths/risks
        strengths = analysis.get("key_strengths") or analysis.get("key_advantages") or []
        if not strengths:
            strengths = [
                "Работающий продукт" if tvl > 0 else "Перспективный концепт",
                "Растущий TVL/пользователи",
            ]
        analysis["key_strengths"] = strengths

        risks = analysis.get("main_risks") or analysis.get("risks") or []
        if not risks:
            if "lending" in category:
                risks = ["Риск дефолта заемщиков", "Уязвимость смарт-контрактов"]
            elif "dex" in category or "yield" in category:
                risks = ["Имперманентные потери", "Взлом смарт-контрактов"]
            else:
                risks = ["Риск низкой ликвидности", "Молодой проект без трек-рекорда"]
        analysis["main_risks"] = risks

        # team/product
        if_missing("team_assessment", "опытная" if tvl > 200_000 else "анонимная/неизвестно")
        if_missing("product_readiness", "работает" if tvl > 0 else "бета/идея")

        # quality default
        if "quality_assessment" not in analysis or not analysis.get("quality_assessment"):
            qa = "высокий" if score_val >= 8 else "средний" if score_val >= 6 else "низкий"
            analysis["quality_assessment"] = qa

        # investment recommendation
        inv = analysis.get("investment_recommendation") or {}
        if "size" not in inv:
            if tvl > 500_000:
                inv["size"] = "$2,000 - $10,000"
            elif tvl > 200_000:
                inv["size"] = "$1,000 - $5,000"
            else:
                inv["size"] = "$500 - $2,000"
        if "entry_strategy" not in inv:
            inv["entry_strategy"] = "Постепенный вход дробно, избегая пиков"
        if "exit_signals" not in inv or not inv.get("exit_signals"):
            inv["exit_signals"] = ["Падение TVL на 40%+", "Существенный баг/взлом"]
        analysis["investment_recommendation"] = inv

        return analysis

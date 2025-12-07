import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List

from backend.analyzer.prompts import (
    ANALYST_PROMPT,
    RISK_PROMPT,
    TECH_PROMPT,
    CHAIRMAN_PROMPT,
)
from backend.config import get_llm_models
from backend.ollama_client import OllamaClient


class CryptoAnalyzer:
    """Анализатор проектов через LLM Council."""

    def __init__(self):
        models_cfg = get_llm_models()
        self.council_models: List[str] = models_cfg.get("council", [])
        self.chairman_model: str = models_cfg.get("chairman", "")
        self.base_url: str = models_cfg.get("base_url", "http://localhost:11434")
        self.analysis_cfg: Dict[str, Any] = models_cfg.get("analysis", {})

    def _normalize_model(self, name: str) -> str:
        """Приводит имя модели к формату с подчеркиваниями (q4_K_M/q4_K_S)."""
        return (
            name.replace("q4KM", "q4_K_M")
            .replace("q4KS", "q4_K_S")
            .replace("::", ":")
        )

    async def analyze_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Полный анализ проекта."""
        temperature = self.analysis_cfg.get("temperature", 0.7)
        num_predict = self.analysis_cfg.get("max_tokens", 2048)
        timeout = self.analysis_cfg.get("analysis_timeout", 120)

        models = [self._normalize_model(m) for m in self.council_models]
        chairman_model = self._normalize_model(self.chairman_model)

        async with OllamaClient(self.base_url).session() as client:
            # Аналитик
            analyst_prompt = ANALYST_PROMPT.format(
                name=project_data.get("name", "Unknown"),
                category=project_data.get("category", "Unknown"),
                description=project_data.get("description", "No description"),
                source=project_data.get("source", "Unknown"),
                metadata=json.dumps(project_data.get("raw_data", {}), indent=2),
            )
            analyst_res = await client.generate(
                models[0],
                analyst_prompt,
                temperature=temperature,
                num_predict=num_predict,
                timeout=timeout,
            )

            # Risk
            risk_prompt = RISK_PROMPT.format(
                project_data=json.dumps(project_data, indent=2)
            )
            risk_res = await client.generate(
                models[1],
                risk_prompt,
                temperature=temperature,
                num_predict=num_predict,
                timeout=timeout,
            )

            # Tech
            tech_prompt = TECH_PROMPT.format(
                project_data=json.dumps(project_data, indent=2)
            )
            tech_res = await client.generate(
                models[2],
                tech_prompt,
                temperature=temperature,
                num_predict=num_predict,
                timeout=timeout,
            )

            # Chairman
            chairman_prompt = CHAIRMAN_PROMPT.format(
                project_name=project_data.get("name", "Unknown"),
                analysis1=analyst_res,
                analysis2=risk_res,
                analysis3=tech_res,
            )
            final_res = await client.generate(
                chairman_model,
                chairman_prompt,
                temperature=temperature,
                num_predict=num_predict,
                timeout=timeout,
            )

        return self._parse_results(analyst_res, risk_res, tech_res, final_res, project_data)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Извлекает JSON из текста LLM."""
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"raw_text": text}
        except json.JSONDecodeError:
            return {"raw_text": text, "error": "invalid_json"}

    def _parse_results(
        self,
        analyst_res: str,
        risk_res: str,
        tech_res: str,
        final_res: str,
        project_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "project_id": project_data.get("id"),
            "project_name": project_data.get("name"),
            "analyst_analysis": self._extract_json(analyst_res),
            "risk_analysis": self._extract_json(risk_res),
            "technical_analysis": self._extract_json(tech_res),
            "final_decision": self._extract_json(final_res),
            "analyzed_at": datetime.now(tz=timezone.utc).isoformat(),
        }

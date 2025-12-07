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
from backend.analyzer.result_parser import extract_json_from_llm_response
from backend.config import get_llm_models
from backend.ollama_client import OllamaClient
from backend.model_checker import check_models
from backend.bot.telegram_logger import log_detailed


class CryptoAnalyzer:
    """Анализатор проектов через LLM Council."""

    def __init__(self):
        models_cfg = get_llm_models()
        self.council_models: List[str] = models_cfg.get("council", [])
        self.chairman_model: str = models_cfg.get("chairman", "")
        self.base_url: str = models_cfg.get("base_url", "http://localhost:11434")
        self.analysis_cfg: Dict[str, Any] = models_cfg.get("analysis", {})
        self._resolved_council: List[str] | None = None
        self._resolved_chairman: str | None = None

    def _normalize_model(self, name: str) -> str:
        """Нормализует имя модели (q4KM->q4_K_M, q4KS->q4_K_S)."""
        return (
            name.replace("q4KM", "q4_K_M")
            .replace("q4KS", "q4_K_S")
            .replace("::", ":")
        )

    async def _resolve_models(self):
        """Определяет доступные модели и подставляет fallback."""
        if self._resolved_council is not None and self._resolved_chairman is not None:
            return

        cfg_models = [self._normalize_model(m) for m in self.council_models if m]
        cfg_chair = self._normalize_model(self.chairman_model) if self.chairman_model else ""

        info = await check_models()
        available = [self._normalize_model(m) for m in info.get("available", []) if m]
        missing = []

        def pick_model(target: str, fallback: str) -> str:
            if target in available:
                return target
            missing.append(target)
            return fallback

        fallback = available[0] if available else (cfg_models[0] if cfg_models else "llama3.2:3b-instruct-q4_K_M")
        resolved = []
        for m in cfg_models[:3]:
            resolved.append(pick_model(m, fallback))
        while len(resolved) < 3:
            resolved.append(fallback)

        chair_resolved = pick_model(cfg_chair or fallback, fallback)

        self._resolved_council = resolved
        self._resolved_chairman = chair_resolved

        await log_detailed(
            "LLM",
            "model_resolution",
            data="; ".join(resolved + [chair_resolved]),
            status=f"missing={len(missing)}",
            details={"missing": ", ".join(missing) if missing else "none", "fallback": fallback},
        )

    async def analyze_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Полный анализ проекта через LLM Council."""
        temperature = self.analysis_cfg.get("temperature", 0.7)
        num_predict = self.analysis_cfg.get("max_tokens", 2048)
        timeout = self.analysis_cfg.get("analysis_timeout", 120)

        await self._resolve_models()
        models = self._resolved_council or []
        chairman_model = self._resolved_chairman or ""

        async with OllamaClient(self.base_url).session() as client:
            analyst_prompt = ANALYST_PROMPT.format(
                project_data=json.dumps(project_data, indent=2),
            )
            analyst_res = await client.generate(
                models[0],
                analyst_prompt,
                temperature=temperature,
                num_predict=num_predict,
                timeout=timeout,
            )

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

            chairman_prompt = CHAIRMAN_PROMPT.format(
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
        return extract_json_from_llm_response(text)

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

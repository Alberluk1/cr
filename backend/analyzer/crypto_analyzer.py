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
        try:
            temperature = self.analysis_cfg.get("temperature", 0.7)
            num_predict = self.analysis_cfg.get("max_tokens", 2048)
            timeout = self.analysis_cfg.get("analysis_timeout", 120)

            await self._resolve_models()
            models = self._resolved_council or []
            chairman_model = self._resolved_chairman or ""

            async with OllamaClient(self.base_url).session() as client:
                async def gen(model_name: str, prompt: str) -> str:
                    try:
                        return await client.generate(
                            model_name,
                            prompt,
                            temperature=temperature,
                            num_predict=num_predict,
                            timeout=timeout,
                        )
                    except Exception as e:
                        return json.dumps({"error": str(e), "model": model_name})

                analyst_prompt = ANALYST_PROMPT.format(
                    project_data=json.dumps(project_data, indent=2),
                )
                analyst_res = await gen(models[0], analyst_prompt)

                risk_prompt = RISK_PROMPT.format(
                    project_data=json.dumps(project_data, indent=2)
                )
                risk_res = await gen(models[1], risk_prompt)

                tech_prompt = TECH_PROMPT.format(
                    project_data=json.dumps(project_data, indent=2)
                )
                tech_res = await gen(models[2], tech_prompt)

                chairman_prompt = CHAIRMAN_PROMPT.format(
                    analysis1=analyst_res,
                    analysis2=risk_res,
                    analysis3=tech_res,
                )
                final_res = await gen(chairman_model, chairman_prompt)

            return self._parse_results(analyst_res, risk_res, tech_res, final_res, project_data)
        except Exception as e:
            return {
                "project_id": project_data.get("id"),
                "project_name": project_data.get("name"),
                "error": f"analyze_exception: {e}",
                "analyzed_at": datetime.now(tz=timezone.utc).isoformat(),
            }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        try:
            res = extract_json_from_llm_response(text)
        except Exception as e:
            return {
                "score": 5.0,
                "score_numeric": 5.0,
                "verdict": "HOLD",
                "error": f"parser_exception: {e}",
                "source": "parser_exception",
            }
        if "score" not in res:
            res["score"] = res.get("score_numeric", 5.0)
        if "score_numeric" not in res:
            res["score_numeric"] = res.get("score", 5.0)
        if "verdict" not in res:
            res["verdict"] = "HOLD"
        return res

    def _parse_results(
        self,
        analyst_res: str,
        risk_res: str,
        tech_res: str,
        final_res: str,
        project_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            analyst_json = self._extract_json(analyst_res)
            risk_json = self._extract_json(risk_res)
            tech_json = self._extract_json(tech_res)
            final_json = self._extract_json(final_res)

            def normalize_final(data: Dict[str, Any]) -> Dict[str, Any]:
                inv = data.get("investment_analysis", {}) if isinstance(data, dict) else {}
                if inv:
                    return {
                        "investment_analysis": {
                            "score_numeric": inv.get("scorenumeric")
                            or inv.get("score")
                            or inv.get("score_numeric")
                            or inv.get("finalscore")
                            or inv.get("final_score"),
                            "verdict": inv.get("verdict"),
                            "reason": inv.get("reason") or inv.get("summary"),
                            "confidence": inv.get("confidence"),
                            "summary": inv.get("summary"),
                        }
                    }
                if isinstance(data, dict):
                    return {
                        "investment_analysis": {
                            "score_numeric": data.get("scorenumeric")
                            or data.get("score")
                            or data.get("score_numeric")
                            or data.get("finalscore")
                            or data.get("final_score"),
                            "verdict": data.get("verdict"),
                            "reason": data.get("reason") or data.get("summary"),
                            "confidence": data.get("confidence"),
                            "summary": data.get("summary"),
                        }
                    }
                return {
                    "investment_analysis": {
                        "score_numeric": None,
                        "verdict": None,
                        "reason": None,
                        "confidence": None,
                        "summary": None,
                    }
                }

            final_normalized = normalize_final(final_json)

            return {
                "project_id": project_data.get("id"),
                "project_name": project_data.get("name"),
                "analyst_analysis": analyst_json,
                "risk_analysis": risk_json,
                "technical_analysis": tech_json,
                "final_decision": final_normalized,
                "analyzed_at": datetime.now(tz=timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "project_id": project_data.get("id"),
                "project_name": project_data.get("name"),
                "error": f"parse_exception: {e}",
                "raw": {
                    "analyst": analyst_res,
                    "risk": risk_res,
                    "tech": tech_res,
                    "final": final_res,
                },
                "analyzed_at": datetime.now(tz=timezone.utc).isoformat(),
            }

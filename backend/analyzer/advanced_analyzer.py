import asyncio
from typing import Dict, Any, List

from backend.config import get_llm_models
from backend.ollama_client import OllamaClient
from backend.analyzer.result_parser import extract_json_from_llm_response
from backend.bot.telegram_logger import log_detailed


class AdvancedAnalyzer:
    """Консенсусный анализатор: опрашивает все модели и берет медиану/среднее."""

    def __init__(self):
        cfg = get_llm_models()
        self.models: List[str] = cfg.get("council", []) or [
            "llama3.2:3b-instruct-q4_K_M"
        ]
        self.base_url = cfg.get("base_url", "http://localhost:11434")

    async def analyze_with_consensus(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            f"Score this crypto project 1-10. Return ONLY a number 1-10.\n\n"
            f"Name: {project_data.get('name','Unknown')}\n"
            f"Category: {project_data.get('category','Unknown')}\n"
            f"Description: {project_data.get('description','')[:400]}\n\n"
            f"Number:"
        )

        async def query(model: str) -> float:
            try:
                async with OllamaClient(self.base_url).session() as client:
                    resp = await client.generate(
                        model=model,
                        prompt=prompt,
                        temperature=0.3,
                        num_predict=16,
                        timeout=20,
                    )
                    parsed = extract_json_from_llm_response(resp)
                    return float(parsed.get("score") or parsed.get("score_numeric") or 5)
            except Exception as e:
                await log_detailed(
                    "ANALYZE",
                    "consensus_error",
                    data=model,
                    status=str(e),
                    level="ERROR",
                )
                return 5.0

        # Параллельные запросы ко всем моделям
        scores = await asyncio.gather(*[query(m) for m in self.models])
        clean_scores = [s for s in scores if isinstance(s, (int, float))]
        if not clean_scores:
            return self._fallback(project_data)

        sorted_scores = sorted(clean_scores)
        median = sorted_scores[len(sorted_scores) // 2]
        avg = sum(clean_scores) / len(clean_scores)
        final_score = round(median * 0.6 + avg * 0.4, 1)

        verdict, confidence = self._verdict_confidence(final_score)

        return {
            "project_id": project_data.get("id"),
            "project_name": project_data.get("name"),
            "score": final_score,
            "verdict": verdict,
            "confidence": confidence,
            "scores": clean_scores,
            "consensus_used": f"{len(clean_scores)} models",
            "analyzed_at": asyncio.get_running_loop().time(),
        }

    def _verdict_confidence(self, score: float) -> (str, str):
        if score >= 8.5:
            return "STRONG_BUY", "HIGH"
        if score >= 7.0:
            return "BUY", "HIGH"
        if score >= 5.5:
            return "HOLD", "MEDIUM"
        if score >= 4.0:
            return "AVOID", "MEDIUM"
        return "SCAM", "LOW"

    def _fallback(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "project_id": project_data.get("id"),
            "project_name": project_data.get("name"),
            "score": 5.0,
            "verdict": "HOLD",
            "confidence": "LOW",
            "scores": [],
            "consensus_used": "fallback",
        }

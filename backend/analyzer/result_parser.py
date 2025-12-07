import json
import re
from typing import Dict, Any


def safe_load_json(text: str) -> Dict[str, Any]:
    """Парсит ЛЮБОЙ ответ LLM, всегда возвращает валидный словарь со score/verdict."""

    if not text or text.strip() == "":
        return {"score": 0, "score_numeric": 0, "verdict": "ERROR", "error": "empty_response"}

    text = text.strip()

    # СЛУЧАЙ 1: Уже валидный JSON c фигурными скобками
    if text.startswith("{") and text.endswith("}"):
        try:
            data = json.loads(text)
            score = (
                data.get("score")
                or data.get("scorenumeric")
                or data.get("Score")
                or data.get("score_numeric")
                or 0
            )
            verdict = data.get("verdict") or data.get("Verdict") or "HOLD"
            res = {
                "score": float(score) if score is not None else 0.0,
                "score_numeric": float(score) if score is not None else 0.0,
                "verdict": str(verdict).upper(),
                "source": "valid_json",
            }
            res.update(data)
            return res
        except Exception:
            pass

    # СЛУЧАЙ 2: строка в кавычках (например '"scorenumeric"')
    if text.startswith('"') and text.endswith('"'):
        inner_text = text[1:-1]
        if "score" in inner_text.lower():
            return {"score": 0.0, "score_numeric": 0.0, "verdict": "HOLD", "source": "score_key_only"}
        return {"score": 0.0, "score_numeric": 0.0, "verdict": "HOLD", "source": "quoted_string"}

    # СЛУЧАЙ 3: Ищем число 1-10 в тексте
    number_match = re.search(r"\b([1-9]|10)(?:\.\d+)?\b", text)
    if number_match:
        score = float(number_match.group(1))
        verdict = "BUY" if score >= 7 else "HOLD" if score >= 5 else "AVOID"
        return {"score": score, "score_numeric": score, "verdict": verdict, "source": "number_in_text"}

    # СЛУЧАЙ 4: Ищем слова BUY/HOLD/AVOID/SCAM
    verdict_match = re.search(r"\b(BUY|HOLD|AVOID|STRONG_BUY|SCAM)\b", text.upper())
    if verdict_match:
        verdict = verdict_match.group(1)
        score_map = {"STRONG_BUY": 9, "BUY": 7, "HOLD": 5, "AVOID": 3, "SCAM": 1}
        return {
            "score": float(score_map.get(verdict, 5)),
            "score_numeric": float(score_map.get(verdict, 5)),
            "verdict": verdict,
            "source": "verdict_in_text",
        }

    # СЛУЧАЙ 5: Упомянут score/scorenumeric/numeric без значения
    if "score" in text.lower() or "numeric" in text.lower():
        return {"score": 0.0, "score_numeric": 0.0, "verdict": "HOLD", "source": "score_mentioned"}

    # Fallback: средняя оценка
    return {
        "score": 0.0,
        "score_numeric": 0.0,
        "verdict": "HOLD",
        "source": "fallback",
        "note": f"Could not parse: {text[:50]}",
    }


# Совместимость со старым названием
def extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    return safe_load_json(text)

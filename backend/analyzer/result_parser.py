import json
import re
from typing import Dict, Any


def safe_load_json(text: str) -> Dict[str, Any]:
    """Парсит любой ответ LLM. Всегда возвращает словарь со score/verdict."""

    if not text or text.strip() == "":
        return {"score": 5, "score_numeric": 5, "verdict": "HOLD", "source": "empty"}

    text = text.strip()

    # Строка в кавычках ("scorenumeric")
    if text.startswith('"') and text.endswith('"'):
        inner = text[1:-1]
        if "score" in inner.lower():
            return {"score": 5, "score_numeric": 5, "verdict": "HOLD", "source": "score_key_only"}
        return {"score": 5, "score_numeric": 5, "verdict": "HOLD", "source": "quoted_string"}

    # Пытаемся распарсить JSON
    if text.startswith("{") and text.endswith("}"):
        try:
            data = json.loads(text)
            score = None
            for k, v in data.items():
                if "score" in k.lower():
                    if isinstance(v, (int, float)):
                        score = float(v)
                        break
            if score is not None:
                verdict = "BUY" if score >= 7 else "HOLD" if score >= 5 else "AVOID"
                out = {"score": score, "score_numeric": score, "verdict": verdict, "source": "json"}
                out.update(data)
                return out
        except Exception:
            pass

    # Ищем число 1-10 в тексте
    match = re.search(r"\b(10|[1-9])\b", text)
    if match:
        score = float(match.group(1))
        verdict = "BUY" if score >= 7 else "HOLD" if score >= 5 else "AVOID"
        return {"score": score, "score_numeric": score, "verdict": verdict, "source": "number"}

    # Fallback
    return {"score": 5, "score_numeric": 5, "verdict": "HOLD", "source": "fallback"}


# Совместимость со старым названием
def extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    return safe_load_json(text)

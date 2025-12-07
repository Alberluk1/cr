import json
import re
from typing import Any, Dict, Tuple


def _to_number(value: Any) -> Tuple[float | None, bool]:
    """Пытается привести значение к числу. Возвращает (число, ok)."""
    if isinstance(value, (int, float)):
        return float(value), True
    if isinstance(value, str):
        try:
            return float(value.strip()), True
        except Exception:
            return None, False
    return None, False


def _normalize(data: Any, raw_text: str) -> Dict[str, Any]:
    """Нормализует ключи и добавляет score_numeric/verdict/summary при наличии."""
    if not isinstance(data, dict):
        data = {"value": data}

    normalized_keys = {}
    for key, val in data.items():
        norm = re.sub(r"[^a-z0-9]", "", str(key).lower())
        normalized_keys[norm] = val

    score = None
    for key in ("scorenumeric", "score", "finalscore", "overall", "rating"):
        if key in normalized_keys:
            score, ok = _to_number(normalized_keys[key])
            if ok:
                break

    verdict = None
    for key in ("verdict", "decision", "ratingtext", "recommendation"):
        if key in normalized_keys and isinstance(normalized_keys[key], str):
            verdict = normalized_keys[key].strip().upper()
            break

    summary = None
    for key in ("summary", "reason", "explanation", "comment"):
        if key in normalized_keys and isinstance(normalized_keys[key], str):
            summary = normalized_keys[key].strip()
            break

    confidence = None
    for key in ("confidence", "confidencelevel"):
        if key in normalized_keys and isinstance(normalized_keys[key], str):
            confidence = normalized_keys[key].strip().upper()
            break

    # Вердикт из текста, если не нашли в JSON-подобных данных
    if verdict is None and raw_text:
        verdict_match = re.search(
            r"\b(STRONG_BUY|BUY|HOLD|AVOID|SCAM)\b", raw_text, re.IGNORECASE
        )
        if verdict_match:
            verdict = verdict_match.group(1).upper()

    # Число из текста, если не нашли в данных
    if score is None and raw_text:
        num_match = re.search(r"\b(10|[0-9](?:\.\d+)?)\b", raw_text)
        if num_match:
            try:
                score = float(num_match.group(1))
            except Exception:
                score = None

    normalized = dict(data)
    if score is not None:
        normalized["score_numeric"] = score
    if verdict is not None:
        normalized["verdict"] = verdict
    if summary is not None:
        normalized.setdefault("summary", summary)
    if confidence is not None:
        normalized.setdefault("confidence", confidence)
    normalized.setdefault("raw_text", raw_text[:500] if raw_text else "")
    return normalized


def _build_dict_from_pairs(text: str) -> Dict[str, Any]:
    """Извлекает пары ключ:значение даже без фигурных скобок."""
    pattern = re.compile(
        r'"?([A-Za-z0-9_\-]+)"?\s*:\s*(".*?"|[-+]?\d+(?:\.\d+)?|true|false|null)',
        re.IGNORECASE | re.DOTALL,
    )
    result: Dict[str, Any] = {}
    for match in pattern.finditer(text):
        key = match.group(1)
        val_raw = match.group(2).strip()
        if val_raw.lower() in ("true", "false", "null"):
            val: Any = {"true": True, "false": False, "null": None}[val_raw.lower()]
        elif val_raw.startswith('"') and val_raw.endswith('"'):
            val = val_raw[1:-1]
        else:
            num, ok = _to_number(val_raw)
            val = num if ok else val_raw
        result[key] = val
    return result


def extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    """
    Пытается извлечь JSON или JSON-подобные данные из ответа LLM.
    Возвращает безопасный словарь с нормализованными ключами.
    """
    raw_text = text or ""
    if not raw_text.strip():
        return {"error": "empty_response", "raw_text": raw_text}

    candidate = raw_text.strip()

    # 1. Пробуем распарсить как есть
    try:
        if candidate.startswith("{") and candidate.endswith("}"):
            return _normalize(json.loads(candidate), raw_text)
    except Exception:
        pass

    # 2. Пробуем выделить подстроку между { ... }
    brace_start = candidate.find("{")
    brace_end = candidate.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        json_str = candidate[brace_start : brace_end + 1]
        try:
            return _normalize(json.loads(json_str), raw_text)
        except Exception:
            # иногда помогает убрать лишние переводы строк и двойные запятые
            compact = re.sub(r",\s*}", "}", re.sub(r"\s+", " ", json_str))
            try:
                return _normalize(json.loads(compact), raw_text)
            except Exception:
                pass

    # 3. Если фигурных скобок нет/поломаны — строим словарь из пар ключ:значение
    pair_dict = _build_dict_from_pairs(candidate)
    if pair_dict:
        return _normalize(pair_dict, raw_text)

    # 4. Числовой ответ без ключей
    num_match = re.search(r"\b(10|[0-9](?:\.\d+)?)\b", candidate)
    if num_match:
        try:
            score = float(num_match.group(1))
            verdict = "BUY" if score >= 7 else "HOLD" if score >= 5 else "AVOID"
            return {
                "score_numeric": score,
                "verdict": verdict,
                "raw_text": raw_text[:500],
            }
        except Exception:
            pass

    # 5. Вердикт без числа
    verdict_match = re.search(
        r"\b(STRONG_BUY|BUY|HOLD|AVOID|SCAM)\b", candidate, re.IGNORECASE
    )
    if verdict_match:
        verdict = verdict_match.group(1).upper()
        score_map = {
            "STRONG_BUY": 9.0,
            "BUY": 7.0,
            "HOLD": 5.0,
            "AVOID": 3.0,
            "SCAM": 1.0,
        }
        return {
            "score_numeric": score_map.get(verdict, 0.0),
            "verdict": verdict,
            "raw_text": raw_text[:500],
        }

    return {"error": "cannot_parse", "raw_text": raw_text[:500]}

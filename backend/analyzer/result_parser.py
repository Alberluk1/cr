import json
import re
from typing import Dict, Any


def _normalize_keys(obj: Any) -> Any:
    """Приводит ключи к нижнему регистру без пробелов/подчеркиваний."""
    if isinstance(obj, dict):
        normalized = {}
        for k, v in obj.items():
            nk = str(k).lower().replace("_", "").replace(" ", "")
            normalized[nk] = _normalize_keys(v)
        return normalized
    if isinstance(obj, list):
        return [_normalize_keys(x) for x in obj]
    return obj


def extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    """Извлекает JSON из ответа LLM даже если есть примеси текста, нормализует ключи."""
    preview = text[:500]
    print(f"RAW LLM RESPONSE (first 500 chars): {preview}")

    cleaned = text.strip()
    # убрать блоки ```json ... ```
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    candidates = []
    if cleaned.startswith("{"):
        candidates.append(cleaned)
    for match in re.finditer(r"\{.*\}", cleaned, re.DOTALL):
        candidates.append(match.group())

    first = cleaned.find("{")
    last = cleaned.rfind("}") + 1
    if first != -1 and last > first:
        candidates.append(cleaned[first:last])

    for cand in candidates:
        try:
            data = json.loads(cand)
            return _normalize_keys(data)
        except Exception:
            continue

    return {"error": "invalid_json", "raw_preview": preview}

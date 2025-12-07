import json
import re
from typing import Dict, Any


def extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    """Извлекает JSON из ответа LLM даже если есть примеси текста."""
    preview = text[:500]
    print(f"RAW LLM RESPONSE (first 500 chars): {preview}")

    cleaned = text.strip()
    # убрать блоки ```json ... ```
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    candidates = []
    # явный блок
    if cleaned.startswith("{"):
        candidates.append(cleaned)
    # любые {...}
    for match in re.finditer(r"\{.*\}", cleaned, re.DOTALL):
        candidates.append(match.group())

    # fallback: первая { и последняя }
    first = cleaned.find("{")
    last = cleaned.rfind("}") + 1
    if first != -1 and last > first:
        candidates.append(cleaned[first:last])

    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception:
            continue

    return {"error": "invalid_json", "raw_preview": preview}

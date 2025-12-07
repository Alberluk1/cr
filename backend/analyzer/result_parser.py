import json
import re
from typing import Dict, Any


def extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    """Извлекает JSON из ответа LLM с примесью текста.

    Стратегия:
    - обрезать кодовые блоки ```json ... ```
    - найти первый/последний фигурные скобки
    - попробовать все кандидаты на парсинг
    - на ошибке вернуть raw_text + error
    """
    cleaned = text.strip()
    # убрать кодовые блоки
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    candidates = []
    # если уже начинается с {
    if cleaned.startswith("{"):
        candidates.append(cleaned)

    # поиск всех блоков {...}
    for match in re.finditer(r"\{.*\}", cleaned, re.DOTALL):
        candidates.append(match.group())

    # попробовать парсить все варианты
    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception:
            continue

    # fallback: попытка убрать всё до первой { и после последней }
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first != -1 and last != -1 and last > first:
        fragment = cleaned[first : last + 1]
        try:
            return json.loads(fragment)
        except Exception:
            pass

    return {"raw_text": text, "error": "invalid_json"}

import json
from typing import Dict, Any


def safe_load_json(text: str) -> Dict[str, Any]:
    """Безопасно парсит JSON, возвращает сырой текст при ошибке."""
    try:
        return json.loads(text)
    except Exception:
        return {"raw_text": text, "error": "invalid_json"}

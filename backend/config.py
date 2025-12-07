import os
import yaml
from functools import lru_cache
from typing import Any, Dict


DEFAULT_CONFIG_PATH = os.getenv("CRYPTO_SCOUT_CONFIG", "config.yaml")
FALLBACK_CONFIG_PATH = "config.example.yaml"


class ConfigError(RuntimeError):
    """Ошибка при загрузке конфигурации."""


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    """Загружает конфигурацию из YAML.

    Приоритет: переменная окружения CRYPTO_SCOUT_CONFIG -> config.yaml -> config.example.yaml.
    """
    paths = [
        DEFAULT_CONFIG_PATH,
        FALLBACK_CONFIG_PATH,
    ]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    raise ConfigError("Не найден файл конфигурации (config.yaml или config.example.yaml)")


def get_llm_models() -> Dict[str, Any]:
    cfg = load_config()
    llm_cfg = cfg.get("llm", {})
    ollama_cfg = llm_cfg.get("ollama", {})
    models_cfg = ollama_cfg.get("models", {})
    return {
        "council": models_cfg.get("council", []),
        "chairman": models_cfg.get("chairman"),
        "base_url": ollama_cfg.get("base_url", "http://localhost:11434"),
        "analysis": llm_cfg.get("analysis", {}),
    }


def get_scanner_config() -> Dict[str, Any]:
    cfg = load_config()
    return cfg.get("scanner", {})


def get_notifications_config() -> Dict[str, Any]:
    cfg = load_config()
    return cfg.get("notifications", {})


def get_db_path() -> str:
    cfg = load_config()
    db = cfg.get("database", {})
    return db.get("path", "data/crypto_projects.db")

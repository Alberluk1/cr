# Crypto Alpha Scout LLM Council

Автономный сканер крипто-проектов с советом LLM (локальные модели через Ollama).

## Быстрый старт
```bash
git clone <repo> crypto-alpha-scout
cd crypto-alpha-scout

# Python
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Конфиг
cp config.example.yaml config.yaml

# БД
python scripts/setup_database.py

# Модели (Linux/macOS; на Windows скачайте вручную)
chmod +x scripts/install_models.sh && ./scripts/install_models.sh
```

Запуск сервиса + API:
```bash
python run.py
# или только API
uvicorn backend.web.routes:app --host 0.0.0.0 --port 8000
```

Основные эндпоинты:
- `GET /health` — проверка
- `GET /projects` — список
- `GET /projects/{id}` — детально
- `POST /scan` — триггер цикла scan+analyze в фоне

## Структура
- `backend/` — FastAPI, сканер, анализатор, уведомления
- `scripts/` — установка моделей, инициализация БД, бэкап
- `data/` — SQLite
- `logs/` — логи
- `frontend/` — перенесите UI из оригинального llm-council

## Ключевые настройки
- `config.yaml` → llm модели, расписание, уведомления Telegram
- Маппинг моделей по умолчанию: `mistral:7b`, `llama3.2:3b`, `qwen2.5:7b`, `gemma2:2b`; председатель = `mistral:7b`.
- Интервал сканирования: `scanner.interval` (сек), лимит проектов: `scanner.max_projects_per_scan`.
- Telegram: включите `notifications.telegram.enabled` и задайте `token`, `chat_id`.

## Заметки
- Анализ выполняется последовательно, чтобы не перегружать RTX 4060 8GB.
- Источники по умолчанию: GitHub + DeFi Llama. Twitter/Discord можно включить в конфиге и дописать сканеры.
- Это аналитический инструмент, а не финансовый совет.

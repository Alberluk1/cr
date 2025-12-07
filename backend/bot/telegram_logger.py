import asyncio
import datetime
from typing import Any, Dict

from backend.telegram_client import send_message


LEVELS = {
    "DEBUG": "🔍",
    "INFO": "🟢",
    "WARNING": "🟡",
    "ERROR": "🔴",
    "CRITICAL": "🔥",
}


async def log(level: str, module: str, message: str) -> None:
    """Быстрая отправка строки с уровнем и модулем."""
    emoji = LEVELS.get(level.upper(), "ℹ️")
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    text = f"{emoji} [{module}] [{ts}]\n{message}"
    await send_message(text)


async def log_detailed(
    module: str,
    action: str,
    data: str = "",
    status: str = "",
    level: str = "INFO",
    details: Dict[str, Any] | None = None,
) -> None:
    """Детальный лог с форматированием."""
    emoji = LEVELS.get(level.upper(), "ℹ️")
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    lines = [
        f"{emoji} [{module}] [{ts}]",
        f"Действие: {action}",
    ]
    if data:
        lines.append(f"Данные: {data}")
    if status:
        lines.append(f"Статус: {status}")
    if details:
        for key, val in details.items():
            lines.append(f"{key}: {val}")
    text = "\n".join(lines)
    await send_message(text)


def fire_and_forget(coro):
    """Запуск корутины без ожидания (для логов, чтобы не блокировать)."""
    try:
        asyncio.get_running_loop().create_task(coro)
    except RuntimeError:
        # Нет активного цикла — запускаем временный
        asyncio.run(coro)

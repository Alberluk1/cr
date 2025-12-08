import os
import aiohttp

# Значения по умолчанию, если переменные окружения не заданы
DEFAULT_TOKEN = "8246586845:AAG2fGI6YZ719M39u_coxcPr1gTf6OVTrqw"
DEFAULT_CHAT_ID = "-4746149710"


async def send_message(
    text: str,
    token: str | None = None,
    chat_id: str | None = None,
    enabled: bool | None = None,
    timeout: int = 10,
    parse_mode: str | None = "Markdown",
) -> bool:
    """
    Отправка простого сообщения в Telegram (aiohttp).
    Возвращает True при статусе 200, иначе False.
    """
    if enabled is False:
        return False

    tok = token or os.getenv("TELEGRAM_BOT_TOKEN", DEFAULT_TOKEN)
    chat = chat_id or os.getenv("TELEGRAM_CHAT_ID", DEFAULT_CHAT_ID)
    enabled_flag = os.getenv("TELEGRAM_ENABLED", "true").lower() != "false"
    if not enabled_flag and enabled is None:
        return False
    if not tok or not chat:
        return False

    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=timeout) as resp:
                return resp.status == 200
    except Exception:
        # Telegram может быть недоступен — просто возвращаем False без исключения
        return False

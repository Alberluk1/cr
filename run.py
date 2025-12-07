#!/usr/bin/env python3
import asyncio
import signal
import sys
import threading

import uvicorn
from uvicorn import Config, Server

from backend.service.main_service import CryptoAlphaService
from backend.web.routes import app
from backend.model_checker import report_models
from backend.bot.telegram_logger import log_detailed


BANNER = """
╔══════════════════════════════════════════════╗
║    CRYPTO ALPHA SCOUT LLM COUNCIL v1.0       ║
║      Automatic Crypto Scanner (local)        ║
╚══════════════════════════════════════════════╝
"""


class MainApplication:
    def __init__(self):
        self.service = CryptoAlphaService()
        self.should_stop = False
        self.server: Server | None = None

    def start_scheduler(self):
        try:
            self.service.run_scheduled()
        except KeyboardInterrupt:
            print("Scheduler stopped")
        except Exception as e:
            print(f"Scheduler error: {e}")

    async def start_api(self):
        config = Config(app=app, host="0.0.0.0", port=8000, log_level="info")
        self.server = Server(config=config)
        await self.server.serve()

    async def startup_checks(self):
        try:
            await report_models()
        except Exception as e:
            await log_detailed("STARTUP", "model_check_failed", status=str(e), level="ERROR")

    async def main(self):
        print(BANNER)
        print("Запуск...")

        def handle_sig(sig, frame):
            print("\nЗавершаем работу...")
            self.should_stop = True
            self.service.stop()
            if self.server:
                self.server.should_exit = True
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_sig)
        signal.signal(signal.SIGTERM, handle_sig)

        # Проверяем модели при старте
        await self.startup_checks()

        # Запуск планировщика в отдельном потоке
        threading.Thread(target=self.start_scheduler, daemon=True).start()

        print("Планировщик запущен")
        print("API сервер запускается на http://localhost:8000")
        print("Документация API: http://localhost:8000/docs")
        print("Для остановки нажмите Ctrl+C\n")

        # API в основном потоке/цикле
        await self.start_api()

    def run(self):
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            print("\nОстановка по запросу пользователя")
        except Exception as e:
            print(f"Ошибка запуска: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    MainApplication().run()

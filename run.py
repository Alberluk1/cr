#!/usr/bin/env python3
import asyncio
import signal
import sys
import threading
import time

import uvicorn
from uvicorn import Config, Server

from backend.service.main_service import CryptoAlphaService
from backend.web.routes import app


class MainApplication:
    def __init__(self):
        self.service = CryptoAlphaService()
        self.should_stop = False
        self.server = None

    def start_scheduler(self):
        """Запуск планировщика в отдельном потоке."""
        try:
            self.service.run_scheduled()
        except KeyboardInterrupt:
            print("Scheduler stopped")
        except Exception as e:
            print(f"Scheduler error: {e}")

    async def start_api(self):
        """Запуск FastAPI сервера."""
        config = Config(app=app, host="0.0.0.0", port=8000, log_level="info")
        self.server = Server(config=config)
        
        # Запускаем сервер
        await self.server.serve()
        
    async def main(self):
        """Основная асинхронная функция."""
        print(
            """
╔══════════════════════════════════════════════╗
║    CRYPTO ALPHA SCOUT LLM COUNCIL v1.0       ║
║      Automatic Crypto Scanner (local)        ║
╚══════════════════════════════════════════════╝
"""
        )
        print("Запуск...")

        # Обработчики сигналов
        def handle_sig(sig, frame):
            print("\nПолучен сигнал, останавливаемся...")
            self.should_stop = True
            self.service.stop()
            if self.server:
                self.server.should_exit = True
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_sig)
        signal.signal(signal.SIGTERM, handle_sig)

        # Запускаем планировщик в отдельном потоке
        scheduler_thread = threading.Thread(target=self.start_scheduler, daemon=True)
        scheduler_thread.start()

        print("Планировщик запущен")
        print("API сервер запускается на http://localhost:8000")
        print("Документация API: http://localhost:8000/docs")
        print("Для остановки нажмите Ctrl+C\n")

        # Запускаем API сервер в основном event loop
        await self.start_api()

    def run(self):
        """Точка входа."""
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            print("\nПриложение остановлено пользователем")
        except Exception as e:
            print(f"Ошибка запуска: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    MainApplication().run()
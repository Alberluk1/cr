#!/usr/bin/env python3
import asyncio
import signal
import sys

from backend.service.main_service import CryptoAlphaService


class MainApplication:
    def __init__(self):
        self.service = CryptoAlphaService()
        self.should_stop = False

    def _handle_sig(self, sig, frame):
        print("\nОстановка по сигналу, завершаем...")
        self.should_stop = True
        self.service.stop()
        sys.exit(0)

    async def main(self):
        signal.signal(signal.SIGINT, self._handle_sig)
        signal.signal(signal.SIGTERM, self._handle_sig)

        # Запускаем циклическое сканирование
        self.service.run_scheduled()

    def run(self):
        asyncio.run(self.main())


if __name__ == "__main__":
    MainApplication().run()

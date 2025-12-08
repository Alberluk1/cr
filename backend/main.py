import asyncio
import logging
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scanner.crypto_scanner import CryptoTracker
from analyzer.advanced_analyzer import AdvancedAnalyzer
from bot.telegram_bot import TelegramBot
import ollama

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("crypto_scanner.log", encoding="utf-8")],
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция с улучшенным выводом"""

    print("\n" + "=" * 60)
    print("🚀 CRYPTO PROJECT SCANNER v2.0")
    print("=" * 60 + "\n")

    try:
        logger.info("⏳ Инициализация компонентов...")

        scanner = CryptoTracker()
        ollama_client = ollama.AsyncClient()
        analyzer = AdvancedAnalyzer(ollama_client)
        bot = TelegramBot()  # Пока без реального бота

        logger.info("🛰️ Запуск сканирования источников...")
        projects = await scanner.run_full_scan()

        if not projects:
            logger.error("❌ Проекты не найдены!")
            return

        logger.info(f"📊 Найдено {len(projects)} проектов")

        max_projects = min(10, len(projects))
        logger.info(f"🔎 Начинаем анализ {max_projects} проектов...\n")

        for i, project in enumerate(projects[:max_projects]):
            try:
                logger.info(f"🔎 Анализ {i+1}/{max_projects}: {project.get('name')} ({project.get('source')})")
                analysis = await analyzer.analyze_project(project)

                if analysis and "score" in analysis:
                    logger.info(f"✅ Анализ завершен: {project.get('name')} score={analysis['score']}")
                    await bot.send_project_analysis(project, analysis)
                else:
                    logger.warning(f"⚠️ Анализ не удался для: {project.get('name')}")

            except Exception as e:
                logger.error(f"❌ Ошибка анализа {project.get('name')}: {e}")
                continue

            if i < max_projects - 1:
                await asyncio.sleep(2)

        logger.info("\n🎯 Анализ завершен успешно!")

    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    try:
        client = ollama.Client()
        models = client.list()
        print(f"🤖 Доступно моделей Ollama: {len(models.models)}")
    except Exception:
        print("❌ Ollama не запущен! Запустите: ollama serve")
        sys.exit(1)

    asyncio.run(main())

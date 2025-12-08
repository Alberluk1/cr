import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scanner.crypto_scanner import CryptoTracker
from analyzer.advanced_analyzer import AdvancedAnalyzer
import ollama

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def main():
    print("\n" + "=" * 50)
    print("🔍 CRYPTO SCANNER - УПРОЩЕННАЯ ВЕРСИЯ")
    print("=" * 50 + "\n")

    try:
        try:
            client = ollama.Client()
            models = client.list()
            print(f"🤖 Моделей Ollama: {len(models['models'])}")
            for model in models["models"][:3]:
                print(f"   • {model['name']}")
            print()
        except Exception:
            print("❌ Запустите Ollama: ollama serve")
            return

        scanner = CryptoTracker()
        ollama_client = ollama.AsyncClient()
        analyzer = AdvancedAnalyzer(ollama_client)

        print("🛰️ Сканируем DeFi Llama...")
        scan_result = await scanner.run_full_scan()
        projects = scan_result if isinstance(scan_result, list) else scan_result.get("projects", [])

        if not projects:
            print("⚠️ Проекты не найдены")
            return

        print(f"\n📊 Найдено {len(projects)} проектов для анализа\n")

        for i, project in enumerate(projects[:5]):
            print(f"{'='*40}")
            print(f"#{i+1} {project['name']}")
            print(f"{'='*40}")

            print(f"📋 Категория: {project.get('category')}")
            print(f"💰 TVL: ${project.get('metrics', {}).get('tvl', 0):,.0f}")

            if project.get("url"):
                print(f"🔗 Сайт: {project.get('url')}")

            print("\n🤖 Анализ LLM...")
            analysis = await analyzer.analyze_project(project)

            if analysis:
                message = f"""
🔍 {project.get('name')}
💰 TVL: ${project.get('metrics', {}).get('tvl', 0):,.0f}
📊 {project.get('category')}
⭐ Оценка: {analysis.get('score')}/10
📈 Вердикт: {analysis.get('verdict')}
💡 {analysis.get('summary')}
🔗 {project.get('url', 'Нет ссылки')}
"""
                print(message)

            print()

            if i < 4:
                await asyncio.sleep(1)

        print("\n✅ Анализ завершен!")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

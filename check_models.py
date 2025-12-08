import ollama
import sys


def check_models():
    """Проверяет какие модели установлены"""
    try:
        client = ollama.Client()
        response = client.list()

        print("📦 УСТАНОВЛЕННЫЕ МОДЕЛИ OLLAMA:")
        print("=" * 40)

        if "models" in response and response["models"]:
            for model in response["models"]:
                print(f"• {model['name']}")
                print(f"  Размер: {model.get('size', 'N/A')}")
                print(f"  Модификация: {model.get('modified_at', 'N/A')}")
                print()
        else:
            print("❌ Модели не найдены")
            print("\nУстановите модели:")
            print("ollama pull llama3.1:8b")
            print("ollama pull mistral:7b")
            print("ollama pull phi3:mini")

        print("=" * 40)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\nЗапустите Ollama:")
        print("1. Откройте новый терминал")
        print("2. Запустите: ollama serve")
        print("3. Вернитесь сюда и запустите снова")


if __name__ == "__main__":
    check_models()

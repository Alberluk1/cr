import json
import logging

import requests

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_deepseek_detailed():
    """Детальный тест DeepSeek API."""
    API_KEY = "sk-e5d551bb7e9642849f7ff975327e5556"
    url = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Ответь просто 'Тест пройден'"}],
        "max_tokens": 50,
    }

    print("=" * 50)
    print("🧪 ДЕТАЛЬНЫЙ ТЕСТ DEEPSEEK API")
    print("=" * 50)

    try:
        print(f"📤 Отправляю запрос на {url}")
        print(f"📝 Данные запроса: {json.dumps(data, ensure_ascii=False)}")

        response = requests.post(url, json=data, headers=headers, timeout=10)

        print(f"\n📥 Получен ответ:")
        print(f"Статус код: {response.status_code}")
        print(f"Заголовки: {dict(response.headers)}")
        print(f"Текст ответа: {response.text}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ УСПЕХ! DeepSeek ответил:")
            print(f"Модель: {result.get('model')}")
            print(f"Ответ: {result['choices'][0]['message']['content']}")
            print(f"Использовано токенов: {result.get('usage', {})}")
        else:
            print(f"\n❌ ОШИБКА {response.status_code}")
            print(f"Ответ сервера: {response.text}")

    except requests.exceptions.Timeout:
        print("\n❌ ТАЙМАУТ: DeepSeek не ответил за 10 секунд")
    except requests.exceptions.ConnectionError:
        print("\n❌ ОШИБКА СОЕДИНЕНИЯ: Не могу подключиться к DeepSeek")
    except Exception as e:
        print(f"\n❌ НЕИЗВЕСТНАЯ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 50)


if __name__ == "__main__":
    test_deepseek_detailed()

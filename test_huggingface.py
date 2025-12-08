import json
import os
import re
import time

import requests

# Ключ берем из окружения
API_KEY = os.getenv("HF_API_KEY", "")


def test_huggingface_api():
    """Тестирует Hugging Face router endpoint на нескольких моделях."""
    print("🧪 ТЕСТ HUGGING FACE API")
    print("=" * 50)

    if not API_KEY:
        print("❌ HF_API_KEY не задан. Установите переменную окружения.")
        return {"success": False}

    test_models = [
        {"name": "TinyLlama (быстрая)", "path": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"},
        {"name": "Mistral 7B", "path": "mistralai/Mistral-7B-Instruct-v0.3"},
    ]

    headers = {"Authorization": f"Bearer {API_KEY}"}

    for model in test_models:
        print(f"\n🔍 Модель: {model['name']}")
        api_url = f"https://router.huggingface.co/{model['path']}"

        prompt = """<|system|>
Ты - тестовый ассистент.</s>
<|user|>
Ответь JSON: {"status": "success", "message": "API работает"}</s>
<|assistant|>
"""

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 100,
                "temperature": 0.1,
                "return_full_text": False,
                "wait_for_model": True,
            },
        }

        print("   📤 Отправляю запрос...")
        start = time.time()
        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
            elapsed = time.time() - start
            print(f"   ⏱️ {elapsed:.2f}s | Статус: {resp.status_code}")
            if resp.status_code == 200:
                result = resp.json()
                if isinstance(result, list) and result:
                    answer = result[0].get("generated_text", str(result))
                    print(f"   ✅ Ответ: {answer[:200]}...")
                    try:
                        match = re.search(r"\{.*\}", answer, re.DOTALL)
                        if match:
                            parsed = json.loads(match.group())
                            print(f"   📊 JSON: {parsed}")
                    except Exception:
                        pass
                else:
                    print(f"   📦 Ответ: {result}")
                return {"success": True, "model": model["path"], "response_time": elapsed}
            elif resp.status_code == 503:
                print("   ⚠️ Модель не загружена (503). Подождите и повторите.")
            else:
                print(f"   ❌ Ошибка: {resp.status_code}")
                print(f"   📄 {resp.text[:500]}")
        except Exception as e:
            print(f"   ❌ Исключение: {e}")

    print("\n❌ Ни одна модель не ответила")
    return {"success": False}


def test_simple_chat():
    """Простой тест TinyLlama."""
    if not API_KEY:
        print("❌ HF_API_KEY не задан.")
        return False
    headers = {"Authorization": f"Bearer {API_KEY}"}
    url = "https://router.huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    payload = {"inputs": "Ответь одним словом: работает", "parameters": {"max_new_tokens": 10, "wait_for_model": True}}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"✅ Ответ: {resp.json()}")
            return True
        print(f"❌ Ответ: {resp.text[:200]}")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    return False


if __name__ == "__main__":
    print("🔑 HF_API_KEY:", "задан" if API_KEY else "не задан")
    result = test_huggingface_api()
    if not result.get("success", False):
        print("\n🔄 Пробую простой тест...")
        test_simple_chat()
    print("\n" + "=" * 50)
    print("🎯 ТЕСТ ЗАВЕРШЕН")

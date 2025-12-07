#!/usr/bin/env python3
import asyncio
import aiohttp
import re


async def test():
    print("🤖 Тестирую Ollama...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Ollama доступен. Моделей: {len(data.get('models', []))}")
                else:
                    print(f"❌ Ollama ошибка: {resp.status}")
                    return
    except Exception as e:
        print(f"❌ Не могу подключиться к Ollama: {e}")
        return

    print("\n🧪 Тестирую LLM запрос...")
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "llama3.2:3b-instruct-q4_K_M",
                "prompt": "Score this crypto project 1-10: Bitcoin. ONLY return a number:",
                "stream": False,
                "options": {"temperature": 0.3},
            }
            async with session.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30,
            ) as resp:
                if resp.status != 200:
                    print(f"❌ LLM ошибка: {resp.status}")
                    return
                result = await resp.json()
                response = result.get("response", "NO RESPONSE")
                print(f"✅ LLM ответил: {response}")
                match = re.search(r"\b([1-9]|10)\b", response)
                if match:
                    print(f"🎯 Нашел оценку: {match.group(1)}/10")
                else:
                    print("⚠️ Не могу найти число в ответе")
    except asyncio.TimeoutError:
        print("⏰ Таймаут LLM запроса (30 сек)")
    except Exception as e:
        print(f"❌ Ошибка теста LLM: {e}")


if __name__ == "__main__":
    asyncio.run(test())

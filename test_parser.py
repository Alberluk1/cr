#!/usr/bin/env python3
from backend.analyzer.result_parser import safe_load_json


def main():
    test_cases = [
        '"scorenumeric"',  # Текущая ошибка
        '{"score": 7, "verdict": "BUY"}',
        '{"scorenumeric": 8}',
        "7",
        "score: 8",
        "BUY",
        "This is a good project, score 9",
        "scorenumeric:",
        "",
        "just text",
    ]

    print("🧪 Тестирую парсер")
    print("=" * 50)
    for i, text in enumerate(test_cases, 1):
        print(f"\nТест {i}: '{text}'")
        result = safe_load_json(text)
        print(f"Результат: {result}")


if __name__ == "__main__":
    main()

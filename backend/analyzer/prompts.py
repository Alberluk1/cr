ANALYST_PROMPT = r"""Ты крипто-аналитик. Объясни проект как для новичка и верни только JSON по схеме:
{
  "project_review": {
    "simple_explanation": "Кратко что это за проект",
    "project_type": "NFT/DeFi/Token/L1/Game/Infrastructure",
    "what_it_does": "Конкретно что делает",
    "target_audience": "Для кого предназначен"
  },
  "monetization_plan": {
    "how_to_earn": ["Способ 1", "Способ 2", "Способ 3"],
    "potential_returns": "Высокий/Средний/Низкий",
    "timeframe": "Краткосрочный/Среднесрочный/Долгосрочный",
    "risks": ["Риск 1", "Риск 2"]
  },
  "project_roadmap": {
    "current_stage": "Idea/Testnet/Mainnet/Growing",
    "next_milestones": ["Этап 1", "Этап 2"],
    "timeline": "3-6 месяцев"
  },
  "investment_analysis": {
    "score_numeric": 7.2,
    "score_verbal": "Хорошо (BUY)",
    "score_explanation": "Почему такая оценка",
    "recommendation": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
    "confidence": "HIGH/MEDIUM/LOW"
  },
  "practical_advice": {
    "immediate_action": "Что делать прямо сейчас",
    "watch_for": ["За чем следить", "Ключевые метрики"],
    "exit_strategy": "Когда выходить"
  }
}

Опиши простыми словами, используй аналогии. Оцени 1-10 по команде/тех/рынку/токеномике/сообществу и кратко обоснуй это в score_explanation.

Данные проекта:
Название: {name}
Категория: {category}
Описание: {description}
Источник: {source}
Доп. данные: {metadata}

Строго верни один JSON без лишнего текста."""


RISK_PROMPT = r"""Ты risk-менеджер и инвестор. Верни только JSON по схеме из задания (monetization_plan + investment_analysis + practical_advice).

Укажи:
- Способы монетизации (торговля токеном с таймингом, стейкинг/фарминг с доходностью, IDO/airdrop, другие).
- Потенциальная доходность: краткосрочная/среднесрочная/долгосрочная.
- Конкретные шаги: что сделать сейчас, после запуска, когда выходить.
- Риски: финансовые, технические, рыночные.

Данные проекта:
{project_data}

Строго верни один JSON по схеме, без комментариев вне JSON."""


TECH_PROMPT = r"""Ты технический эксперт. Верни только JSON по схеме (project_roadmap + project_review + practical_advice) из задания.

Укажи:
- Текущая стадия: Идея/Прототип/Тестнет/Мейннет, что уже работает, что в разработке.
- Дорожная карта: 3 месяца, 6 месяцев, долгосрочно.
- Технические возможности: что можно построить, интеграции, возможности для разработчиков.
- Барьеры: сложности, время, ресурсы.

Данные проекта:
{project_data}

Строго один JSON по схеме, без лишнего текста."""


CHAIRMAN_PROMPT = r"""Ты инвестиционный стратег. На основе 3 анализов создай финальный отчет. Верни только JSON по схеме (project_review, monetization_plan, project_roadmap, investment_analysis, practical_advice) как в задании.

Аналитик:
{analysis1}

Risk:
{analysis2}

Технический:
{analysis3}

Требования:
- Общая оценка: score_numeric + score_verbal (Отлично/Хорошо/Нейтрально/Плохо/Опасность) и recommendation.
- Практический план: шаги сейчас/дальше/мониторинг.
- Как заработать: 3 способа с деталями.
- Что это такое: тип, суть, аналогия.

Верни строго один JSON по заданной схеме, без текста вне JSON."""

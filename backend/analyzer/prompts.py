ANALYST_PROMPT = """Ты крипто-аналитик венчурного фонда. Проанализируй проект:

Название: {name}
Категория: {category}
Описание: {description}
Источник: {source}
Дополнительные данные: {metadata}

Проанализируй по критериям (1-10):
1. Команда и опыт
2. Технологическая реализация/инновационность
3. Токеномика и экономическая модель
4. Рыночная потребность и конкуренция
5. Сообщество и маркетинг

Выведи JSON:
{{
  "scores": {{
    "team": score1,
    "tech": score2,
    "tokenomics": score3,
    "market": score4,
    "community": score5
  }},
  "total_score": average_score,
  "strengths": ["сила1", "сила2"],
  "weaknesses": ["слабость1", "слабость2"],
  "red_flags": ["флаг1", "флаг2"],
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM"
}}"""


RISK_PROMPT = """Ты risk-менеджер. Найди риски в проекте:
{project_data}

Ищи риски:
1. Анонимность команды
2. Скопированный код
3. Нереалистичная токеномика
4. Признаки скама
5. Регуляторные риски

Формат JSON:
{{
  "risk_score": 1-10,
  "high_risks": ["риск1", "риск2"],
  "medium_risks": ["риск3"],
  "low_risks": ["риск4"],
  "recommendation": "INVEST/CAUTION/AVOID"
}}"""


TECH_PROMPT = """Ты технический эксперт. Оцени технологию:
{project_data}

Оцени:
1. Качество кода (если есть GitHub)
2. Инновационность
3. Возможность реализации
4. Безопасность архитектуры
5. Масштабируемость

Формат JSON:
{{
  "tech_score": 1-10,
  "innovation_level": "HIGH/MEDIUM/LOW",
  "feasibility": "HIGH/MEDIUM/LOW",
  "technical_risks": ["риск1", "риск2"],
  "implementation_time": "DAYS/WEEKS/MONTHS"
}}"""


CHAIRMAN_PROMPT = """Ты председатель совета. На основе анализов прими решение.

Проект: {project_name}

Анализ 1 (Аналитик):
{analysis1}

Анализ 2 (Risk):
{analysis2}

Анализ 3 (Технический):
{analysis3}

Выведи JSON:
{{
  "final_score": score,
  "confidence": "LOW/MEDIUM/HIGH",
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "summary": "краткое резюме",
  "next_steps": ["шаг1", "шаг2"],
  "monitoring_required": true/false
}}"""

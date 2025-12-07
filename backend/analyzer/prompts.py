# Упрощенные промпты: просим только число 1-10
ANALYST_PROMPT = """Score this project 1-10.\n\nName: {name}\nCategory: {category}\nSource: {source}\n\nReturn ONLY a number between 1 and 10.\n\nNumber:"""

RISK_PROMPT = """Risk level 1-10 for this project.\n\nName: {name}\nCategory: {category}\nSource: {source}\n\nReturn ONLY a number between 1 and 10.\n\nNumber:"""

TECH_PROMPT = """Technical strength 1-10 for this project.\n\nName: {name}\nCategory: {category}\nSource: {source}\n\nReturn ONLY a number between 1 and 10.\n\nNumber:"""

CHAIRMAN_PROMPT = """Final investment score 1-10 for this project.\n\nName: {name}\nCategory: {category}\nSource: {source}\n\nReturn ONLY a number between 1 and 10.\n\nNumber:"""

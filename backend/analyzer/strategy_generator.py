from typing import Dict, List


class StrategyGenerator:
    """Генератор инвестиционных стратегий на основе категории и оценки."""

    def generate_strategy(self, project: Dict, score: float) -> Dict:
        category = (project.get("category") or "").lower()
        score = float(score or 0)

        strategy = {
            "risk_level": "",
            "capital_allocation": "",
            "immediate_actions": [],
            "short_term": [],
            "medium_term": [],
            "long_term": [],
            "monitoring_metrics": [],
            "exit_signals": [],
        }

        # Уровень риска и аллокация
        if score >= 8:
            strategy["risk_level"] = "НИЗКИЙ"
            strategy["capital_allocation"] = "5-10% от портфеля"
        elif score >= 6:
            strategy["risk_level"] = "СРЕДНИЙ"
            strategy["capital_allocation"] = "2-5% от портфеля"
        else:
            strategy["risk_level"] = "ВЫСОКИЙ"
            strategy["capital_allocation"] = "0.5-2% от портфеля"

        # Общие немедленные действия
        strategy["immediate_actions"] = [
            "Добавить в watchlist",
            "Создать канал мониторинга",
            "Установить алерты на ключевые метрики",
        ]

        # Категориальные стратегии
        if "defi" in category:
            strategy["immediate_actions"] += [
                "Изучить документацию",
                "Проверить аудит контрактов",
                "Анализировать динамику TVL",
            ]
            if score >= 8:
                strategy["short_term"] = [
                    "Рассмотреть участие в liquidity mining",
                    "Мониторить анонсы партнерств",
                    "Настроить алерты на изменение TVL",
                ]
                strategy["medium_term"] = [
                    "Диверсифицировать в несколько пулов",
                    "Участвовать в governance",
                    "Реинвестировать rewards",
                ]
        elif "nft" in category or "game" in category:
            strategy["immediate_actions"] += [
                "Изучить roadmap проекта",
                "Проверить команду и предыдущие работы",
                "Анализировать engagement сообщества",
            ]
            if score >= 7:
                strategy["short_term"] = [
                    "Участвовать в whitelist если есть",
                    "Мониторить Discord активность",
                    "Анализировать вторичный рынок",
                ]
        elif "infra" in category or "infrastructure" in category or "l1" in category:
            strategy["immediate_actions"] += [
                "Протестировать продукт если доступно",
                "Проверить GitHub активность",
                "Изучить конкурентов",
            ]
            if score >= 8:
                strategy["short_term"] = [
                    "Ждать тестнет запуска",
                    "Мониторить бета-тестеров",
                    "Следить за партнерскими анонсами",
                ]

        strategy["monitoring_metrics"] = self._get_metrics_for_category(category, project)
        strategy["exit_signals"] = self._get_exit_signals(score)
        return strategy

    def _get_metrics_for_category(self, category: str, project: Dict) -> List[str]:
        metrics = [
            "Активность разработки (GitHub)",
            "Рост community (соцсети)",
            "Упоминания в медиа",
        ]
        if "defi" in category:
            metrics += [
                "TVL (динамика)",
                "APY/APR доходности",
                "Уникальные пользователи",
                "Объем торгов",
            ]
        elif "nft" in category or "game" in category:
            metrics += [
                "Объем торгов на маркетплейсах",
                "Количество уникальных держателей",
                "Floor price динамика",
                "Активность в игре",
            ]
        elif "infra" in category or "infrastructure" in category or "l1" in category:
            metrics += [
                "Количество транзакций",
                "Активные адреса",
                "Комиссии сети",
                "Интеграции с другими проектами",
            ]
        return metrics

    def _get_exit_signals(self, score: float) -> List[str]:
        if score >= 8:
            return [
                "Падение TVL на 50%+",
                "Выход ключевых разработчиков",
                "Критическая уязвимость",
                "Резкое падение активности",
            ]
        else:
            return [
                "Отсутствие развития 2+ месяца",
                "Падение community активности",
                "Невыполнение roadmap",
                "Появление сильных конкурентов",
            ]

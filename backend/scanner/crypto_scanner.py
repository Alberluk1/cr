import asyncio
import logging
from typing import Dict, List, Any

import aiohttp

logger = logging.getLogger(__name__)


class CryptoTracker:
    def __init__(self):
        self.defillama_url = "https://api.llama.fi/protocols"

    async def scan_defi_llama(self) -> List[Dict[str, Any]]:
        """Сканирует только DeFi Llama для новых малых проектов"""
        projects: List[Dict[str, Any]] = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.defillama_url, timeout=15) as response:
                    if response.status != 200:
                        logger.error(f"❌ Ошибка DeFi Llama API: {response.status}")
                        return projects

                    all_protocols = await response.json()

                    for protocol in all_protocols:
                        try:
                            name = (protocol.get("name") or "").strip()
                            if not name:
                                continue

                            tvl = float(protocol.get("tvl", 0) or 0)
                            category = (protocol.get("category") or "").lower()
                            slug = protocol.get("slug", "")

                            exclude_categories = ["bridge", "stablecoin", "cex", "services", ""]

                            if (
                                tvl > 0
                                and tvl < 5_000_000
                                and category not in exclude_categories
                                and name != "Illuvium"
                                and len(name) > 2
                            ):
                                links = {
                                    "website": protocol.get("url", ""),
                                    "twitter": protocol.get("twitter", ""),
                                    "github": protocol.get("github", ""),
                                    "telegram": protocol.get("telegram", ""),
                                    "discord": protocol.get("discord", ""),
                                    "docs": "",
                                }
                                links = {k: v for k, v in links.items() if v and v.strip()}

                                project = {
                                    "id": f"defillama_{slug}",
                                    "name": name,
                                    "description": protocol.get("description", "DeFi protocol"),
                                    "category": category.capitalize(),
                                    "source": "defillama",
                                    "url": protocol.get("url", ""),
                                    "links": links,
                                    "metrics": {
                                        "tvl": tvl,
                                        "tvl_change_7d": protocol.get("change_7d", 0),
                                        "chain": protocol.get("chain", "Multi-Chain"),
                                        "audits": len(protocol.get("audit_links", []) or []),
                                        "is_audited": len(protocol.get("audit_links", []) or []) > 0,
                                    },
                                    "raw_data": protocol,
                                }

                                projects.append(project)
                                logger.info(
                                    f"✅ Найден: {name} | TVL: ${tvl:,.0f} | Категория: {category}"
                                )

                        except Exception as e:
                            logger.debug(f"Ошибка обработки протокола: {e}")
                            continue

                    projects = sorted(projects, key=lambda x: x["metrics"]["tvl"])[:30]
                    logger.info(f"🎯 Отфильтровано {len(projects)} проектов")

        except Exception as e:
            logger.error(f"❌ Ошибка сканирования: {e}")

        return projects

    async def run_full_scan(self) -> List[Dict[str, Any]]:
        """Основная функция - ТОЛЬКО DeFi Llama (возвращает dict совместимо с сервисом)."""
        logger.info("🛰️ Запуск сканирования DeFi Llama...")

        projects = await self.scan_defi_llama()

        if projects:
            logger.info(f"📊 Сканирование завершено, найдено {len(projects)} проектов")
            logger.info(f"• defillama: {len(projects)}")
        else:
            logger.warning("⚠️ Проекты не найдены")

        return {"projects": projects, "source_counts": {"defillama": len(projects)}}

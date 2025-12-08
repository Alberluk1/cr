import logging
from typing import Any, Dict, List

import aiohttp

logger = logging.getLogger(__name__)


class CryptoTracker:
    """Сканер источников (пока только DeFi Llama)."""

    def __init__(self):
        self.defillama_url = "https://api.llama.fi/protocols"

    async def _make_request(self, url: str) -> Any:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    logger.error(f"HTTP {response.status} для {url}")
            except Exception as e:
                logger.error(f"Ошибка запроса {url}: {e}")
        return None

    async def scan_defi_llama(self) -> List[Dict[str, Any]]:
        """Отбираем малые/новые проекты DeFi Llama."""
        projects: List[Dict[str, Any]] = []
        data = await self._make_request(self.defillama_url)
        if not data:
            return projects

        for protocol in data:
            try:
                name = (protocol.get("name") or "").strip()
                if not name or len(name) < 2:
                    continue

                tvl = float(protocol.get("tvl", 0) or 0)
                category = (protocol.get("category") or "").lower()
                slug = protocol.get("slug", "")

                exclude_categories = {
                    "bridge",
                    "stablecoin",
                    "cex",
                    "services",
                    "ponzi",
                    "reserve currency",
                    "algo-stables",
                    "farm",
                    "indexes",
                    "derivatives",
                    "synthetics",
                }
                allowed_categories = {"defi", "dex", "lending", "yield", "infrastructure", "nft", "gaming"}
                tvl_valid = 50_000 < tvl < 1_000_000
                growth_valid = float(protocol.get("change_7d", 0) or 0) > 0
                category_valid = category in allowed_categories
                has_links = protocol.get("url") and protocol.get("url").strip()

                if not (tvl_valid and category_valid and has_links and growth_valid):
                    continue

                links = {}
                for key in ["url", "twitter", "github", "telegram", "discord"]:
                    val = protocol.get(key)
                    if val:
                        links[key] = val

                change_7d = float(protocol.get("change_7d", 0) or 0)
                token_symbol = protocol.get("tokenSymbol") or protocol.get("symbol")

                project = {
                    "id": f"defillama_{slug}",
                    "name": name,
                    "description": protocol.get("description", f"{category.capitalize()} protocol"),
                    "category": category.capitalize(),
                    "source": "defillama",
                    "url": protocol.get("url", ""),
                    "token_symbol": token_symbol,
                    "links": links,
                    "metrics": {
                        "tvl": tvl,
                        "tvl_change_7d": change_7d,
                        "chain": protocol.get("chain", "Multi-Chain"),
                        "audits": len(protocol.get("audit_links", []) or []),
                        "is_audited": len(protocol.get("audit_links", []) or []) > 0,
                    },
                    "raw_data": protocol,
                }
                projects.append(project)
            except Exception as e:
                logger.debug(f"Пропускаем {protocol.get('name', 'unknown')}: {e}")
                continue

        projects.sort(key=lambda x: x["metrics"]["tvl"])
        projects = projects[:15]
        logger.info(f"Отобрано {len(projects)} качественных проектов")
        return projects

    async def run_full_scan(self) -> Dict[str, Any]:
        logger.info("Сканирование DeFi Llama...")
        projects = await self.scan_defi_llama()
        if projects:
            logger.info(f"Найдено {len(projects)} проектов")
        else:
            logger.warning("Проекты не найдены")
        return {"projects": projects, "source_counts": {"defillama": len(projects)}}

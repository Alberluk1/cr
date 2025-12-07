#!/usr/bin/env python3
import asyncio
import json
import time

from backend.config import get_llm_models
from backend.ollama_client import OllamaClient
from backend.telegram_client import send_message


async def test_model(model: str, prompt: str = "test") -> dict:
    client = OllamaClient()
    async with client.session():
        start = time.time()
        try:
            resp = await client.generate(model, prompt, timeout=20)
            return {"model": model, "ok": True, "duration": time.time() - start, "resp": resp[:120]}
        except Exception as e:
            return {"model": model, "ok": False, "error": str(e), "duration": time.time() - start}


async def main():
    cfg = get_llm_models()
    models = cfg.get("council", []) + [cfg.get("chairman")]
    models = [m for m in models if m]
    results = []
    for m in models:
        results.append(await test_model(m))
    lines = ["🧪 [DIAGNOSE MODELS]"]
    for r in results:
        if r["ok"]:
            lines.append(f"🟢 {r['model']} ok ({r['duration']:.1f}s)")
        else:
            lines.append(f"🔴 {r['model']} fail ({r['duration']:.1f}s): {r.get('error')}")
    await send_message("\n".join(lines))


if __name__ == "__main__":
    asyncio.run(main())

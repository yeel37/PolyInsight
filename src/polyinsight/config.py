"""
PolyInsight 配置
使用 Polymarket 完全公开的 Gamma REST API，无需任何密钥/钱包
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve()
for _ in range(6):
    if (PROJECT_ROOT / "data").exists():
        break
    PROJECT_ROOT = PROJECT_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Gamma API（公开）
GAMMA_API_BASE = "https://gamma-api.polymarket.com"
DEFAULT_LIMIT = 25

# 可选 AI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "") or os.getenv("XAI_API_KEY", "")
ENABLE_AI = bool(OPENAI_API_KEY or GROK_API_KEY)

print(f"[PolyInsight] Gamma API: {GAMMA_API_BASE} | AI增强: {'启用' if ENABLE_AI else '本地规则'}")

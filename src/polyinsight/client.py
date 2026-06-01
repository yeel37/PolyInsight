"""
Polymarket Gamma API 客户端
完全公开接口 + 离线回退数据集（首次/网络失败必备）
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import requests
import pandas as pd

from .config import GAMMA_API_BASE, DEFAULT_LIMIT, DATA_DIR

FALLBACK_FILE = DATA_DIR / "polymarket_fallback.json"


def _get_fallback_data() -> List[Dict[str, Any]]:
    """内置高质量回退数据（模拟 8 个热门市场）"""
    now = datetime.now().isoformat()
    return [
        {
            "id": "fallback-1",
            "question": "2025年美国总统大选，特朗普是否获胜？",
            "slug": "presidential-election-winner-2025",
            "active": True,
            "closed": False,
            "volume": 48500000,
            "liquidity": 3200000,
            "outcomes": json.dumps([
                {"name": "Yes", "price": 0.58},
                {"name": "No", "price": 0.42}
            ]),
            "endDate": "2025-11-05T00:00:00Z",
            "category": "Politics",
            "lastTradePrice": 0.58,
            "updatedAt": now
        },
        {
            "id": "fallback-2",
            "question": "比特币2025年底是否突破12万美元？",
            "slug": "btc-120k-eoy-2025",
            "active": True,
            "closed": False,
            "volume": 18700000,
            "liquidity": 980000,
            "outcomes": json.dumps([
                {"name": "Yes", "price": 0.37},
                {"name": "No", "price": 0.63}
            ]),
            "endDate": "2025-12-31T23:59:59Z",
            "category": "Crypto",
            "lastTradePrice": 0.37,
            "updatedAt": now
        },
        {
            "id": "fallback-3",
            "question": "美联储2025年是否会降息至少3次？",
            "slug": "fed-rate-cuts-2025",
            "active": True,
            "closed": False,
            "volume": 9200000,
            "liquidity": 410000,
            "outcomes": json.dumps([
                {"name": "Yes", "price": 0.71},
                {"name": "No", "price": 0.29}
            ]),
            "endDate": "2025-12-18T00:00:00Z",
            "category": "Finance",
            "lastTradePrice": 0.71,
            "updatedAt": now
        },
        {
            "id": "fallback-4",
            "question": "2025年Q3苹果iPhone出货量是否超预期？",
            "slug": "apple-iphone-q3-2025",
            "active": True,
            "closed": False,
            "volume": 3400000,
            "liquidity": 180000,
            "outcomes": json.dumps([
                {"name": "Yes", "price": 0.49},
                {"name": "No", "price": 0.51}
            ]),
            "endDate": "2025-10-25T00:00:00Z",
            "category": "Tech",
            "lastTradePrice": 0.49,
            "updatedAt": now
        }
    ]


def fetch_active_markets(limit: int = DEFAULT_LIMIT, tag: str = None) -> List[Dict[str, Any]]:
    """
    获取活跃市场
    优先真实 API，失败自动返回 fallback
    """
    params = {
        "active": "true",
        "closed": "false",
        "limit": str(limit),
        "order": "volume",
        "ascending": "false"
    }
    if tag:
        params["tag"] = tag

    try:
        resp = requests.get(f"{GAMMA_API_BASE}/markets", params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            # 保存一份作为新 fallback
            try:
                FALLBACK_FILE.parent.mkdir(exist_ok=True)
                FALLBACK_FILE.write_text(json.dumps(data[:8], ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
            return data
    except Exception as e:
        print(f"[PolyInsight] API 请求失败，使用离线数据: {e}")

    # 回退
    if FALLBACK_FILE.exists():
        try:
            return json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return _get_fallback_data()


def normalize_market(m: Dict[str, Any]) -> Dict[str, Any]:
    """统一字段，便于下游使用"""
    try:
        outcomes = json.loads(m.get("outcomes", "[]")) if isinstance(m.get("outcomes"), str) else m.get("outcomes", [])
    except Exception:
        outcomes = []

    yes_price = 0.5
    for o in outcomes or []:
        if isinstance(o, dict):
            name = str(o.get("name", "")).lower()
            if name in ("yes", "是"):
                yes_price = float(o.get("price", 0.5))
                break
        elif isinstance(o, str) and "yes" in o.lower():
            # 容错：某些 API 返回简化格式
            try:
                yes_price = float(o.split(":")[-1].strip(" }\"")) if ":" in o else 0.5
            except Exception:
                pass
    if (not outcomes or yes_price == 0.5) and "lastTradePrice" in m:
        yes_price = float(m.get("lastTradePrice", 0.5))

    return {
        "id": m.get("id") or m.get("slug"),
        "question": m.get("question", "未知市场"),
        "slug": m.get("slug", ""),
        "yes_price": round(yes_price, 4),
        "no_price": round(1 - yes_price, 4),
        "volume": float(m.get("volume", 0)),
        "liquidity": float(m.get("liquidity", 0)),
        "category": m.get("category", "Other"),
        "end_date": m.get("endDate", "")[:10] if m.get("endDate") else "N/A",
        "active": m.get("active", True),
        "updated": m.get("updatedAt", "")[:16] if m.get("updatedAt") else ""
    }


def get_top_markets(limit: int = 12) -> pd.DataFrame:
    """返回标准化 DataFrame，供 Streamlit/CLI 使用"""
    raw = fetch_active_markets(limit)
    normalized = [normalize_market(m) for m in raw[:limit]]
    df = pd.DataFrame(normalized)
    if not df.empty:
        df = df.sort_values("volume", ascending=False).reset_index(drop=True)
    return df


def generate_mock_history(yes_price: float, days: int = 14) -> pd.DataFrame:
    """为可视化生成合理的历史走势（正弦+噪声）"""
    import numpy as np
    import pandas as pd
    dates = pd.date_range(end=datetime.now().date(), periods=days, freq="D")
    noise = np.random.normal(0, 0.03, days)
    trend = np.linspace(-0.08, 0.05, days)
    prices = np.clip(yes_price + trend + noise, 0.05, 0.95)
    return pd.DataFrame({"date": dates, "yes_price": np.round(prices, 4)})

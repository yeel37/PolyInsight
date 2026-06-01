#!/usr/bin/env python3
"""
PolyInsight CLI
快速查看 Polymarket 热门市场 + AI 建议 + 导出 CSV
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
from datetime import datetime

try:
    from .client import get_top_markets
    from .analyzer import analyze_market, generate_market_insights
    from .config import REPORTS_DIR
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.polyinsight.client import get_top_markets
    from src.polyinsight.analyzer import analyze_market, generate_market_insights
    from src.polyinsight.config import REPORTS_DIR


def main():
    parser = argparse.ArgumentParser(description="PolyInsight - Polymarket 智能分析工具")
    parser.add_argument("--limit", "-l", type=int, default=10, help="获取市场数量")
    parser.add_argument("--export", "-e", action="store_true", help="导出 CSV 报告")
    parser.add_argument("--tag", type=str, default=None, help="按标签过滤 (如 Politics, Crypto)")
    args = parser.parse_args()

    print("🔮 PolyInsight - Polymarket 预测市场数据 + AI 分析")
    print("=" * 60)

    df = get_top_markets(args.limit)
    if df.empty:
        print("❌ 无法获取数据")
        return

    print(f"\n📈 热门市场 Top {len(df)}（按成交量排序）\n")
    for _, row in df.iterrows():
        print(f"• {row['question'][:55]}...")
        print(f"  Yes概率: {row['yes_price']*100:.1f}% | 成交: ${row['volume']:,.0f} | 结束: {row['end_date']}")
        print()

    insights = generate_market_insights(df)
    print("🧠 全局洞察：")
    for i in insights:
        print(f"  {i}")

    if args.export:
        out = REPORTS_DIR / f"polymarket_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"\n✅ 报告已导出: {out}")


if __name__ == "__main__":
    main()

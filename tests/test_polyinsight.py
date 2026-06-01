"""
PolyInsight 基础自检
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from polyinsight.client import get_top_markets
from polyinsight.analyzer import generate_market_insights


def test_fetch_and_analyze():
    df = get_top_markets(6)
    assert not df.empty
    assert "yes_price" in df.columns
    insights = generate_market_insights(df)
    assert len(insights) >= 1


if __name__ == "__main__":
    print("Running PolyInsight self-check...")
    test_fetch_and_analyze()
    print("✅ PolyInsight 核心自检通过（含离线回退）!")

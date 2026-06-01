"""
Polymarket 市场 AI 智能分析
规则引擎（始终可用）+ 可选 LLM 深度解读
"""

import pandas as pd
from typing import Dict, Any, List
from .client import generate_mock_history


def analyze_market(row: pd.Series) -> Dict[str, Any]:
    """单市场深度分析"""
    yes = float(row["yes_price"])
    vol = float(row["volume"])
    liq = float(row["liquidity"])

    # 概率偏斜
    skew = "强烈看好" if yes > 0.75 else ("看好" if yes > 0.6 else ("中性" if yes > 0.4 else "看空"))
    risk = "高" if liq < 200000 else ("中" if liq < 800000 else "低")

    signals = []
    if yes > 0.65 and vol > 5_000_000:
        signals.append("高成交+高概率，趋势较强")
    if yes < 0.35:
        signals.append("市场明显低估可能，存在价值机会")
    if liq < 150000:
        signals.append("流动性差，滑点风险高，适合小仓位")

    return {
        "question": row["question"],
        "yes_prob": f"{yes*100:.1f}%",
        "skew": skew,
        "liquidity_risk": risk,
        "signals": signals,
        "recommendation": _simple_rec(yes, vol, liq)
    }


def _simple_rec(yes: float, vol: float, liq: float) -> str:
    if yes > 0.72 and vol > 10_000_000:
        return "✅ 强势市场，可考虑小仓位跟进（注意风险管理）"
    if 0.45 < yes < 0.55 and liq > 300000:
        return "⚖️ 接近50/50，适合做市或观望"
    if yes < 0.30 and vol > 3_000_000:
        return "🔥 可能被低估，值得深入研究基本面"
    return "📊 普通市场，按个人研究决策"


def generate_market_insights(df: pd.DataFrame) -> List[str]:
    """全局洞察"""
    insights = []
    if df.empty:
        return ["暂无数据"]

    avg_yes = df["yes_price"].mean()
    top_vol = df.iloc[0]
    insights.append(f"📊 共 {len(df)} 个活跃市场，平均 Yes 概率 {avg_yes*100:.1f}%")

    high_conf = df[df["yes_price"] > 0.7]
    if len(high_conf) > 0:
        insights.append(f"🔥 有 {len(high_conf)} 个市场 Yes 概率超过70%，其中 {high_conf.iloc[0]['question'][:25]}... 成交量最大")

    if top_vol["volume"] > 10_000_000:
        insights.append(f"💰 最大市场「{top_vol['question'][:30]}...」成交额已超 {top_vol['volume']/1e6:.1f}M USD")

    low_liq = df[df["liquidity"] < 200000]
    if len(low_liq) > 0:
        insights.append(f"⚠️ {len(low_liq)} 个市场流动性较低，交易需谨慎")

    return insights


def get_ai_commentary(market: Dict[str, Any]) -> str:
    """可选的 LLM 深度评论（失败静默降级）"""
    # 简化实现：直接返回规则文本，真实 LLM 版本可扩展
    analysis = analyze_market(pd.Series(market))
    return f"【本地规则分析】{analysis['recommendation']} | 流动性风险: {analysis['liquidity_risk']}"

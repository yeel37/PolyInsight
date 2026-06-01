"""
PolyInsight Streamlit 界面
实时抓取 Polymarket 热门市场 + 概率可视化 + AI 分析 + 一键导出
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "src"))

from polyinsight.client import get_top_markets, generate_mock_history
from polyinsight.analyzer import analyze_market, generate_market_insights
from polyinsight.config import ENABLE_AI

st.set_page_config(page_title="PolyInsight - Polymarket AI 分析", page_icon="🔮", layout="wide")
st.title("🔮 PolyInsight")
st.caption("Polymarket 公开数据抓取 · 实时概率 · AI 智能分析 · 历史走势 · CSV 报告")

@st.cache_data(ttl=180)
def load_markets(limit: int):
    return get_top_markets(limit)

with st.sidebar:
    limit = st.slider("获取市场数量", 5, 30, 12)
    if st.button("🔄 立即刷新数据", type="primary"):
        st.cache_data.clear()
        st.rerun()
    st.caption("数据来源：Polymarket Gamma 公开 API（无需登录）")
    st.info("AI 增强：" + ("已启用" if ENABLE_AI else "本地规则模式"))

df = load_markets(limit)

if df.empty:
    st.error("数据加载失败，请检查网络或稍后重试")
    st.stop()

# 表格
st.subheader("📊 实时市场概率（按成交量排序）")
st.dataframe(
    df[["question", "yes_price", "volume", "liquidity", "category", "end_date"]],
    use_container_width=True,
    column_config={
        "yes_price": st.column_config.NumberColumn("Yes 概率", format="%.2f"),
        "volume": st.column_config.NumberColumn("成交量 $", format="%,.0f"),
    }
)

# 洞察
st.subheader("🧠 AI 洞察")
for line in generate_market_insights(df):
    st.markdown(f"- {line}")

# 单市场详情 + 历史模拟
st.subheader("🔍 市场详情与走势模拟")
selected = st.selectbox("选择市场", df["question"].tolist())
row = df[df["question"] == selected].iloc[0]

analysis = analyze_market(row)
col1, col2 = st.columns(2)
with col1:
    st.metric("Yes 概率", f"{row['yes_price']*100:.1f}%")
    st.metric("No 概率", f"{row['no_price']*100:.1f}%")
    st.write("**分析结论**:", analysis["recommendation"])
with col2:
    st.write("**信号**:", ", ".join(analysis["signals"]) or "暂无特别信号")
    st.write("**流动性风险**:", analysis["liquidity_risk"])

# 模拟历史
hist = generate_mock_history(row["yes_price"])
fig = px.line(hist, x="date", y="yes_price", title=f"「{selected[:40]}...」模拟价格走势（仅供参考）")
fig.update_yaxes(range=[0, 1])
st.plotly_chart(fig, use_container_width=True)

# 导出
if st.button("📥 导出当前报告为 CSV"):
    out = ROOT / "reports" / f"polyinsight_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
    out.parent.mkdir(exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    st.success(f"已保存 {out.name}")

st.caption("PolyInsight v1.0 | 数据 100% 来自公开 API | 分析仅供参考，不构成投资建议")

"""⚗️ 배합비 설계"""
import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
# Streamlit Cloud 호환 경로
PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(PAGE_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
from data.common import *

st.set_page_config(page_title="배합비설계", page_icon="⚗️", layout="wide")
st.markdown("# ⚗️ 배합비 상세 설계")
st.markdown("---")

form = st.session_state.get("ai_formulation")

if not form:
    st.warning("먼저 [🤖 AI제품카드] 페이지에서 제품을 선택하세요.")
    if st.button("🤖 AI 카드로 이동"):
        st.switch_page("pages/3_🤖_AI제품카드.py")
    st.stop()

st.markdown(f"### {form['productName']}")
st.caption(form["concept"])

c1, c2 = st.columns([2, 1])

with c1:
    # 파이 차트
    ing_data = [{"원료": i["name"], "비율": i["pct"]} for i in form["ingredients"] if i["pct"] > 0]
    fig = px.pie(pd.DataFrame(ing_data), values="비율", names="원료", hole=0.4,
                 color_discrete_sequence=COLORS)
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

    # 바 차트
    bar_df = pd.DataFrame(ing_data).sort_values("비율", ascending=True)
    fig2 = px.bar(bar_df, y="원료", x="비율", orientation="h", color="원료",
                  color_discrete_sequence=COLORS, text="비율")
    fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig2.update_layout(height=300, showlegend=False, xaxis_title="비율 (%)")
    st.plotly_chart(fig2, use_container_width=True)

with c2:
    st.metric("🧪 Brix", f"{form['brix']}°")
    st.metric("⚗️ pH", f"{form['pH']}")
    st.metric("🔥 칼로리", f"{form['calories']}kcal")
    st.metric("📅 유통기한", form["shelfLife"])
    st.metric("📦 기준용량", form["totalVolume"])

    st.markdown("---")
    if st.button("🏭 공정 설계로 이동 →", use_container_width=True, type="primary"):
        st.switch_page("pages/5_🏭_공정리스크.py")
    if st.button("✏️ 배합 연습으로 이동 →", use_container_width=True):
        csv_text = "원료명,함량(g),비율(%),기능,등급\n"
        for ing in form["ingredients"]:
            csv_text += f"{ing['name']},{ing['amount']},{ing['pct']},{ing['function']},{ing['grade']}\n"
        st.session_state.practice_csv = csv_text
        st.switch_page("pages/7_✏️_배합연습.py")

# 상세 테이블
st.markdown("---")
st.markdown("### 📋 원료 상세")
ing_df = pd.DataFrame(form["ingredients"])
ing_df.columns = ["원료명", "함량", "비율(%)", "기능", "등급"]
st.dataframe(ing_df, use_container_width=True, hide_index=True)

# CSV 다운로드
csv = ing_df.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 배합표 CSV 다운로드", csv, f"{form['productName']}_배합표.csv", "text/csv")

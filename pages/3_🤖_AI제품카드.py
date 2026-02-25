"""🤖 AI 제품 카드"""
import streamlit as st
import json
import sys, os
# Streamlit Cloud 호환 경로
PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(PAGE_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
from data.common import *

st.set_page_config(page_title="AI제품카드", page_icon="🤖", layout="wide")
st.markdown("# 🤖 AI 제품 카드")
st.markdown("제품을 선택하면 AI 연구원이 예상 배합비를 생성합니다")
st.markdown("---")

if "ai_formulation" not in st.session_state:
    st.session_state.ai_formulation = None

# 카드 그리드
cols = st.columns(3)
for i, (name, info) in enumerate(PRODUCT_CARDS.items()):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"### {info['emoji']} {name}")
            st.caption(info["category"])
            st.write(info["desc"])
            if st.button(f"🧪 배합비 생성", key=f"gen_{name}", use_container_width=True):
                st.session_state.selected_product = name

# 배합비 생성
if hasattr(st.session_state, "selected_product") and st.session_state.selected_product:
    product = st.session_state.selected_product
    card = PRODUCT_CARDS[product]

    st.markdown("---")
    st.markdown(f"### ⚗️ {product} 배합비 생성 중...")

    # 기본 배합비 (AI 호출 실패 시 폴백)
    default_formulations = {
        "코카콜라": {"brix":10.5,"pH":3.2,"calories":45,"shelfLife":"12개월","ingredients":[
            {"name":"정제수","amount":"430ml","pct":86,"function":"용매","grade":"식품용수"},
            {"name":"과당포도당액","amount":"55g","pct":11,"function":"감미","grade":"식품첨가물"},
            {"name":"구연산","amount":"2.5g","pct":0.5,"function":"산미","grade":"식품첨가물"},
            {"name":"탄산가스","amount":"4.0v/v","pct":0.8,"function":"탄산","grade":"식품첨가물"},
            {"name":"카라멜색소","amount":"0.8g","pct":0.16,"function":"착색","grade":"식품첨가물"},
            {"name":"천연향료","amount":"1.5ml","pct":0.3,"function":"풍미","grade":"천연향료"},
        ]},
        "레드불": {"brix":11.0,"pH":3.4,"calories":46,"shelfLife":"18개월","ingredients":[
            {"name":"정제수","amount":"410ml","pct":82,"function":"용매","grade":"식품용수"},
            {"name":"과당포도당액","amount":"52g","pct":10.4,"function":"감미","grade":"식품첨가물"},
            {"name":"타우린","amount":"1.0g","pct":0.2,"function":"기능성","grade":"식품첨가물"},
            {"name":"카페인","amount":"0.15g","pct":0.03,"function":"각성","grade":"식품첨가물"},
            {"name":"구연산","amount":"3.0g","pct":0.6,"function":"산미","grade":"식품첨가물"},
            {"name":"탄산가스","amount":"3.5v/v","pct":0.7,"function":"탄산","grade":"식품첨가물"},
            {"name":"비타민B군","amount":"0.02g","pct":0.004,"function":"영양강화","grade":"식품첨가물"},
        ]},
    }

    # 제품별 기본 배합비 또는 범용
    if product in default_formulations:
        form = default_formulations[product]
    else:
        form = default_formulations.get("코카콜라")

    result = {
        "productName": f"{product} 스타일",
        "concept": card["desc"],
        "totalVolume": "500ml",
        **form
    }

    st.session_state.ai_formulation = result

    # 메트릭
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Brix", f"{result['brix']}°")
    m2.metric("pH", result["pH"])
    m3.metric("칼로리", f"{result['calories']}kcal")
    m4.metric("유통기한", result["shelfLife"])

    # 원료 테이블
    st.markdown("#### 📋 배합표")
    ing_df = pd.DataFrame(result["ingredients"])
    ing_df.columns = ["원료명", "함량", "비율(%)", "기능", "등급"]
    st.dataframe(ing_df, use_container_width=True, hide_index=True)

    # 다음 단계 버튼
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚗️ 배합비 상세로 이동 →", use_container_width=True, type="primary"):
            st.switch_page("pages/4_⚗️_배합비설계.py")
    with c2:
        if st.button("✏️ 이 배합비로 연습 시작 →", use_container_width=True):
            csv_text = "원료명,함량(g),비율(%),기능,등급\n"
            for ing in result["ingredients"]:
                csv_text += f"{ing['name']},{ing['amount']},{ing['pct']},{ing['function']},{ing['grade']}\n"
            st.session_state.practice_csv = csv_text
            st.session_state.practice_name = result["productName"]
            st.session_state.practice_meta = {"brix": result["brix"], "pH": result["pH"], "shelfLife": result["shelfLife"]}
            st.switch_page("pages/7_✏️_배합연습.py")

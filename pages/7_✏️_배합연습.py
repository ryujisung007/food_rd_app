"""✏️ 배합비 작성 연습"""
import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os, io
# Streamlit Cloud 호환 경로
PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(PAGE_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
from data.common import *

st.set_page_config(page_title="배합연습", page_icon="✏️", layout="wide")
st.markdown("# ✏️ 배합비 작성 연습")
st.markdown("CSV 직접 작성 또는 파일 업로드 → 실시간 파싱 → 검증 → 저장·다운로드")
st.markdown("---")

student = st.session_state.get("student_name", "")

# ━━━ 사이드바: 샘플 & 저장 목록 ━━━
with st.sidebar:
    st.markdown("### 📎 샘플 배합비")
    for name in SAMPLE_FORMULATIONS:
        if st.button(f"📋 {name}", key=f"smp_{name}", use_container_width=True):
            st.session_state.csv_input = SAMPLE_FORMULATIONS[name]
            st.session_state.formula_name = name
            st.rerun()

    st.markdown("---")
    st.markdown("### 💾 저장된 배합비")
    saved = load_saved_formulas()
    if saved:
        for s in saved[:10]:
            label = f"{s['name']} ({s.get('student','?')}) {s['timestamp'][:10]}"
            if st.button(f"📂 {label}", key=f"load_{s['filename']}", use_container_width=True):
                # 저장된 배합비를 CSV로 복원
                df_s = pd.DataFrame(s["ingredients"])
                csv_buf = df_s.to_csv(index=False)
                st.session_state.csv_input = csv_buf
                st.session_state.formula_name = s["name"]
                st.rerun()
    else:
        st.caption("아직 저장된 배합비가 없습니다")

# ━━━ AI 카드에서 넘어온 경우 ━━━
if "practice_csv" in st.session_state:
    if "csv_input" not in st.session_state or not st.session_state.get("csv_input"):
        st.session_state.csv_input = st.session_state.practice_csv
        st.session_state.formula_name = st.session_state.get("practice_name", "AI 배합비")
    del st.session_state.practice_csv

# ━━━ 제품 기본정보 ━━━
with st.expander("📋 제품 기본정보", expanded=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    formula_name = c1.text_input("제품명", value=st.session_state.get("formula_name", "나의 배합비"))
    volume = c2.text_input("기준용량(ml)", value="500")
    brix = c3.text_input("목표 Brix(°)", placeholder="예: 10.5")
    pH_val = c4.text_input("목표 pH", placeholder="예: 3.5")
    shelf = c5.text_input("유통기한", placeholder="예: 12개월")

# ━━━ 좌우 레이아웃 ━━━
left, right = st.columns([1, 1])

with left:
    st.markdown("### 📝 CSV 입력")

    # 파일 업로드
    uploaded = st.file_uploader("CSV 파일 업로드", type=["csv", "txt"], label_visibility="collapsed")
    if uploaded:
        content = uploaded.read().decode("utf-8-sig")
        st.session_state.csv_input = content
        st.rerun()

    # 텍스트 에디터
    csv_text = st.text_area(
        "배합비 CSV (직접 입력 또는 수정)",
        value=st.session_state.get("csv_input", ""),
        height=300,
        placeholder="원료명,함량(g),비율(%),기능,등급\n정제수,430,86.0,용매,식품용수\n과당포도당액,55,11.0,감미,식품첨가물\n...",
        key="csv_editor",
    )
    st.session_state.csv_input = csv_text

    # 버튼 행
    b1, b2, b3 = st.columns(3)
    do_validate = b1.button("🔍 검증", use_container_width=True, type="primary")
    do_save = b2.button("💾 저장", use_container_width=True)
    do_clear = b3.button("🗑️ 초기화", use_container_width=True)

    if do_clear:
        st.session_state.csv_input = ""
        st.session_state.formula_name = "나의 배합비"
        st.rerun()


with right:
    # 파싱
    df_parsed, msg = parse_csv_formula(csv_text)

    if df_parsed is not None:
        st.markdown(f"### 📊 배합표 ({len(df_parsed)}종 원료)")

        # 비율 합계
        if "비율(%)" in df_parsed.columns:
            total_pct = df_parsed["비율(%)"].sum()
            color = "green" if 99 <= total_pct <= 101 else "red"
            st.markdown(f"**비율 합계: :{color}[{total_pct:.1f}%]**")

        # 테이블
        st.dataframe(df_parsed, use_container_width=True, hide_index=True)

        # 파이 차트
        if "비율(%)" in df_parsed.columns and "원료명" in df_parsed.columns:
            pie_df = df_parsed[df_parsed["비율(%)"] > 0]
            if len(pie_df) > 0:
                fig = px.pie(pie_df, values="비율(%)", names="원료명", hole=0.4,
                             color_discrete_sequence=COLORS)
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

        # ━━━ 검증 ━━━
        if do_validate:
            meta = {}
            if brix: meta["brix"] = float(brix)
            if pH_val: meta["pH"] = float(pH_val)

            result = validate_formula(df_parsed, meta)

            if result["passed"]:
                st.success("✅ 검증 통과!")
            else:
                st.error("⚠️ 수정이 필요합니다")

            for iss in result["issues"]:
                st.error(f"❌ {iss}")
            for w in result["warnings"]:
                st.warning(f"⚠️ {w}")

        # ━━━ 저장 ━━━
        if do_save:
            if not student:
                st.warning("⚠️ 메인 페이지에서 이름을 먼저 입력하세요")
            else:
                meta = {"brix": brix, "pH": pH_val, "volume": volume, "shelfLife": shelf}
                filepath = save_formula(formula_name, df_parsed, meta, student)
                st.success(f"✅ 저장 완료! ({os.path.basename(filepath)})")

        # ━━━ 다운로드 ━━━
        st.markdown("---")
        st.markdown("### 📥 다운로드")
        c1, c2 = st.columns(2)
        with c1:
            csv_dl = df_parsed.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 CSV", csv_dl, f"{formula_name}.csv", "text/csv", use_container_width=True)
        with c2:
            buf = io.BytesIO()
            df_parsed.to_excel(buf, index=False, engine="openpyxl")
            st.download_button("📥 Excel", buf.getvalue(), f"{formula_name}.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             use_container_width=True)

    elif csv_text.strip():
        st.error(f"❌ 파싱 오류: {msg}")
    else:
        st.info("""
        **입력 방법:**
        1. 좌측 텍스트 영역에 CSV 직접 작성
        2. CSV 파일 업로드
        3. 사이드바에서 샘플 배합비 불러오기
        4. AI 카드에서 생성된 배합비 가져오기

        **CSV 형식:**
        ```
        원료명,함량(g),비율(%),기능,등급
        정제수,430,86.0,용매,식품용수
        과당포도당액,55,11.0,감미,식품첨가물
        ```
        """)

# app.py
from __future__ import annotations
import streamlit as st

from core import calculate_all
from validations import validate_input
from io_json import export_input_json, import_input_json
from export_pdf import make_pdf_bytes
import ui

st.set_page_config(page_title="退職金・年金受取最適化シミュレーター v4.4", layout="wide")
ui.inject_css()

if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0
if "input_defaults" not in st.session_state:
    st.session_state.input_defaults = {
        "currentAge": , "retirementAge": 0, "joinAge": 0, "serviceYears": 0,
        "severancePay": 0.0,
        "dcStartAge": 0, "dcEndAge": 0, "dcCurrentBalance": 0.0, "dcMonthlyContribution": 0.0, "dcReturnRate": 0.0,
        "idecoStartAge": 0, "idecoEndAge": 0, "idecoCurrentBalance": 0.0, "idecoMonthlyContribution": 0.0, "idecoReturnRate": 0.0,
        "currentSalary": 0.0, "avgSalary": 0.0,
        "pensionExemption": False,
        "endAge": 90,
    }
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_errors" not in st.session_state:
    st.session_state.last_errors = []

# Simple tab switch control
choice = st.radio("", ["📝 情報入力", "📊 シミュレーション結果"], index=st.session_state.active_tab, horizontal=True, label_visibility="collapsed")
st.session_state.active_tab = 0 if choice.startswith("📝") else 1

ui.render_shell_start(st.session_state.active_tab)

if st.session_state.active_tab == 0:
    with st.expander("📥 入力復元（JSONアップロード） / 📤 入力保存（JSONダウンロード）", expanded=False):
        uploaded = st.file_uploader("JSONファイルを選択", type=["json"])
        if uploaded is not None:
            try:
                restored = import_input_json(uploaded.read().decode("utf-8"))
                st.session_state.input_defaults = {**st.session_state.input_defaults, **restored}
                st.success("入力を復元しました。フォームに反映されています。")
            except Exception as e:
                st.error(f"JSONの読み込みに失敗しました: {e}")
        st.download_button(
            "入力をJSONとしてダウンロード",
            data=export_input_json(st.session_state.input_defaults).encode("utf-8"),
            file_name="retirement_input.json",
            mime="application/json",
        )

    submitted, input_internal = ui.render_input_form(st.session_state.input_defaults)

    if submitted:
        errs = validate_input(input_internal)
        st.session_state.last_errors = errs
        if errs:
            st.error("入力に不備があります。以下をご確認ください：\n- " + "\n- ".join(errs))
        else:
            st.session_state.last_result = calculate_all(input_internal)
            st.session_state.input_defaults = input_internal
            st.success("計算が完了しました。結果タブをご覧ください。")
            st.session_state.active_tab = 1
            st.rerun()
else:
    if st.session_state.last_errors:
        st.warning("前回の入力に警告/エラーがあります。入力タブで修正してください。")
    if st.session_state.last_result is None:
        st.info("まだ計算結果がありません。『情報入力』タブで入力して計算してください。")
    else:
        # 結果から入力へ戻る（再計算用）
        if st.button("📝 情報入力に戻る", use_container_width=True):
            st.session_state.active_tab = 0
            st.rerun()
        res = st.session_state.last_result
        strategies = res["strategies"]
        best = res["best"]
        input_ = res["input"]
        pdf = make_pdf_bytes(input_, strategies, best)
        st.download_button(
            "📄 PDFを出力（おすすめ戦略＋比較表＋入力条件）",
            data=pdf,
            file_name="retirement_optimization_result.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        ui.render_results(strategies, best, input_, res["publicPensionAnnual"])

ui.render_shell_end()

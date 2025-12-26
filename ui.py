# ui.py
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import streamlit as st
from core import safe_number, build_pension_component_monthly
import textwrap

def inject_css():
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def render_shell_start(active_tab: int):
    st.markdown('<div class="mz-container">', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="mz-header">
          <h1>💰 退職金・年金受取最適化シミュレーター</h1>
          <p>税負担を最小化し、手取りを最大化する最適な受取戦略を見つけましょう</p>
          <p style="margin-top: 12px; font-size: 13px; opacity: 0.95; line-height: 1.5;">
            本システムでは、退職年齢に応じて受取戦略を切り替えています。<br>
            FIRE層では、19年ルールに基づき退職から20年後に一時金受取年齢を固定し、<br>
            年金は生涯実効税率が最小となる開始年齢を選択します。
          </p>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    tab0_cls = "mz-tab active" if active_tab == 0 else "mz-tab"
    tab1_cls = "mz-tab active" if active_tab == 1 else "mz-tab"
    st.markdown(
        f'''
        <div class="mz-tabs">
          <div class="{tab0_cls}">📝 情報入力</div>
          <div class="{tab1_cls}">📊 シミュレーション結果</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="padding:30px;">', unsafe_allow_html=True)

def render_shell_end():
    st.markdown("</div></div>", unsafe_allow_html=True)

def _num(x: Any) -> str:
    try: return f"{round(float(x)):,}"
    except Exception: return "0"

def _num1(x: Any) -> str:
    try: return f"{float(x):.1f}"
    except Exception: return "0.0"

def render_input_form(defaults: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    with st.form("simulatorForm", clear_on_submit=False):
        st.markdown('<div class="mz-section"><h2>👤 基本情報</h2>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            currentAge = st.number_input("現在の年齢", min_value=0, max_value=120, value=int(defaults.get("currentAge", 0)), step=1, key="currentAge")
        with c2:
            retirementAge = st.number_input("退職予定年齢", min_value=0, max_value=120, value=int(defaults.get("retirementAge", 0)), step=1, key="retirementAge")
        with c3:
            joinAge = st.number_input("入社年齢", min_value=0, max_value=120, value=int(defaults.get("joinAge", 0)), step=1, key="joinAge")
        with c4:
            serviceYears = st.number_input("勤続年数（年）", min_value=0, max_value=80, value=int(defaults.get("serviceYears", 0)), step=1, key="serviceYears")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="mz-section"><h2>💼 退職金情報</h2>', unsafe_allow_html=True)
        severancePay = st.number_input("退職金見込額（万円）", min_value=0.0, value=float(defaults.get("severancePay", 0.0)), step=1.0, key="severancePay")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="mz-section"><h2>🏢 企業型DC（確定拠出年金）</h2>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            dcStartAge = st.number_input("加入開始年齢", min_value=0, max_value=120, value=int(defaults.get("dcStartAge", 0)), step=1, key="dcStartAge")
        with c2:
            dcEndAge = st.number_input("拠出終了年齢", min_value=0, max_value=120, value=int(defaults.get("dcEndAge", 0)), step=1, key="dcEndAge")
        with c3:
            dcCurrentBalance = st.number_input("現在の評価額（万円）", min_value=0.0, value=float(defaults.get("dcCurrentBalance", 0.0)), step=1.0, key="dcCurrentBalance")
        with c4:
            dcMonthlyContribution = st.number_input("月次拠出額（万円）", min_value=0.0, value=float(defaults.get("dcMonthlyContribution", 0.0)), step=0.1, key="dcMonthlyContribution")
        dcReturnRate_pct = st.number_input("想定年利率（%）", min_value=0.0, value=float(defaults.get("dcReturnRate", 0.0))*100.0, step=0.1, key="dcReturnRate_pct")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="mz-section"><h2>🏦 iDeCo（個人型確定拠出年金）</h2>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            idecoStartAge = st.number_input("加入開始年齢 ", min_value=0, max_value=120, value=int(defaults.get("idecoStartAge", 0)), step=1, key="idecoStartAge")
        with c2:
            idecoEndAge = st.number_input("拠出終了年齢 ", min_value=0, max_value=120, value=int(defaults.get("idecoEndAge", 0)), step=1, key="idecoEndAge")
        with c3:
            idecoCurrentBalance = st.number_input("現在の評価額（万円） ", min_value=0.0, value=float(defaults.get("idecoCurrentBalance", 0.0)), step=1.0, key="idecoCurrentBalance")
        with c4:
            idecoMonthlyContribution = st.number_input("月次拠出額（万円） ", min_value=0.0, value=float(defaults.get("idecoMonthlyContribution", 0.0)), step=0.1, key="idecoMonthlyContribution")
        idecoReturnRate_pct = st.number_input("想定年利率（%） ", min_value=0.0, value=float(defaults.get("idecoReturnRate", 0.0))*100.0, step=0.1, key="idecoReturnRate_pct")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="mz-section"><h2>💵 給与・年金情報</h2>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            currentSalary = st.number_input("現在の年収（万円）", min_value=0.0, value=float(defaults.get("currentSalary", 0.0)), step=1.0, key="currentSalary")
        with c2:
            avgSalary = st.number_input("平均標準報酬月額（万円）", min_value=0.0, value=float(defaults.get("avgSalary", 0.0)), step=1.0, key="avgSalary")
        pensionExemption = st.selectbox(
            "60歳未満退職時の国民年金保険料免除",
            options=["免除なし（全額納付）", "免除あり（半額換算）"],
            index=1 if defaults.get("pensionExemption", False) else 0,
            key="pensionExemption"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="mz-section"><h2>⚙️ その他設定</h2>', unsafe_allow_html=True)
        endAge = st.number_input("計算終了年齢（受給終了年齢）", min_value=0, max_value=130, value=int(defaults.get("endAge", 90)), step=1, key="endAge")
        st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("💡 最適戦略を計算する", use_container_width=True)

    input_internal = {
        "currentAge": int(currentAge),
        "retirementAge": int(retirementAge),
        "joinAge": int(joinAge),
        "serviceYears": int(serviceYears),
        "severancePay": float(severancePay),

        "dcStartAge": int(dcStartAge),
        "dcEndAge": int(dcEndAge),
        "dcCurrentBalance": float(dcCurrentBalance),
        "dcMonthlyContribution": float(dcMonthlyContribution),
        "dcReturnRate": float(dcReturnRate_pct) / 100.0,

        "idecoStartAge": int(idecoStartAge),
        "idecoEndAge": int(idecoEndAge),
        "idecoCurrentBalance": float(idecoCurrentBalance),
        "idecoMonthlyContribution": float(idecoMonthlyContribution),
        "idecoReturnRate": float(idecoReturnRate_pct) / 100.0,

        "currentSalary": float(currentSalary),
        "avgSalary": float(avgSalary),
        "pensionExemption": (pensionExemption == "免除あり（半額換算）"),
        "endAge": int(endAge),
    }
    return submitted, input_internal

def render_results(strategies: List[Dict[str, Any]], best: Dict[str, Any], input_: Dict[str, Any], public_pension_annual: float):
    cards_html = ""
    for s in strategies:
        is_rec = (s["code"] == best["code"])
        card_cls = "result-card recommended" if is_rec else "result-card"
        eff = (s["totalTax"]/s["totalGross"]*100) if s["totalGross"]>0 else 0.0
        cards_html += textwrap.dedent(f'''
        <div class="{card_cls}">
          <h3>{s["name"]}{("<span class=\"badge\">おすすめ</span>" if is_rec else "")}</h3>
          <p style="color:#666; margin-bottom:20px;">{s["description"]}</p>
          <div class="result-grid">
            <div class="result-item"><label>総受取額（税引前）</label><span class="value">{_num(s["totalGross"])}万円</span></div>
            <div class="result-item"><label>総税負担</label><span class="value">{_num(s["totalTax"])}万円</span></div>
            <div class="result-item"><label>総手取額</label><span class="value orange">{_num(s["totalNet"])}万円</span></div>
            <div class="result-item"><label>実効税率</label><span class="value">{eff:.1f}%</span></div>
          </div>
          <div class="result-grid" style="margin-top:15px;">
            <div class="result-item"><label>60〜65歳 年金額面月収</label><span class="value">{_num1(s["monthlyIncome60to65Gross"])}万円</span></div>
            <div class="result-item"><label>60〜65歳 年金手取り月収</label><span class="value">{_num1(s["monthlyIncome60to65Net"])}万円</span></div>
            <div class="result-item"><label>65歳以降 年金額面月収</label><span class="value">{_num1(s["monthlyIncome65plusGross"])}万円</span></div>
            <div class="result-item"><label>65歳以降 年金手取り月収</label><span class="value">{_num1(s["monthlyIncome65plusNet"])}万円</span></div>
          </div>
        ''').lstrip()
        lumps = s.get("lumpsum") or []
        if lumps:
            cards_html += textwrap.dedent('''
            <div class="lumpsum-detail">
              <h4>📋 一時金内訳</h4>
              <div class="lumpsum-item" style="background:#e0e7ff; font-weight:bold; margin-bottom:8px;">
                <span>項目（年齢）</span><span style="text-align:right;">額面</span><span style="text-align:right;">税金</span><span style="text-align:right;">手取り</span>
              </div>
            ''').lstrip()
            for it in lumps:
                cards_html += textwrap.dedent(f'''
                <div class="lumpsum-item">
                  <div class="lumpsum-label">{it["item"]}<br><span class="lumpsum-age">({int(it["age"])}歳)</span></div>
                  <div class="lumpsum-amount">{_num(it["amount"])}万円</div>
                  <div class="lumpsum-tax">{_num(it["tax"])}万円</div>
                  <div class="lumpsum-net">{_num(it["net"])}万円</div>
                </div>
                ''').lstrip()
            total_amount = sum(safe_number(it.get("amount"),0) for it in lumps)
            total_tax = sum(safe_number(it.get("tax"),0) for it in lumps)
            total_net = sum(safe_number(it.get("net"),0) for it in lumps)
            cards_html += textwrap.dedent(f'''
              <div class="lumpsum-item total">
                <div class="lumpsum-label">一時金合計</div>
                <div class="lumpsum-amount">{_num(total_amount)}万円</div>
                <div class="lumpsum-tax">{_num(total_tax)}万円</div>
                <div class="lumpsum-net" style="font-size:20px;">{_num(total_net)}万円</div>
              </div>
            </div>
            ''').lstrip()
        cards_html += "</div>"

    st.markdown('<div class="mz-section"><h2>🎯 おすすめ戦略</h2>', unsafe_allow_html=True)
    st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    by_code = {s["code"]: s for s in strategies}
    A,B,C,D = by_code["A"], by_code["B"], by_code["C"], by_code["D"]
    best_code = best["code"]

    def th(code, label):
        cls = "highlight-orange-header" if code==best_code else ""
        return f'<th class="{cls}">{label}</th>'
    def td(code, content):
        cls = "highlight-orange-cell" if code==best_code else ""
        return f'<td class="{cls}">{content}</td>'

    table_html = f'''
    <table class="mz-table">
      <tr>
        <th>項目</th>
        {th("A","戦略A")}
        {th("B","戦略B")}
        {th("C","戦略C")}
        {th("D","戦略D")}
      </tr>
      <tr>
        <td>総手取額</td>
        {td("A", _num(A["totalNet"])+"万円")}
        {td("B", _num(B["totalNet"])+"万円")}
        {td("C", _num(C["totalNet"])+"万円")}
        {td("D", _num(D["totalNet"])+"万円")}
      </tr>
      <tr>
        <td>総税負担</td>
        {td("A", _num(A["totalTax"])+"万円")}
        {td("B", _num(B["totalTax"])+"万円")}
        {td("C", _num(C["totalTax"])+"万円")}
        {td("D", _num(D["totalTax"])+"万円")}
      </tr>
      <tr>
        <td>実効税率</td>
        {td("A", f'{(A["totalTax"]/A["totalGross"]*100 if A["totalGross"]>0 else 0):.1f}%')}
        {td("B", f'{(B["totalTax"]/B["totalGross"]*100 if B["totalGross"]>0 else 0):.1f}%')}
        {td("C", f'{(C["totalTax"]/C["totalGross"]*100 if C["totalGross"]>0 else 0):.1f}%')}
        {td("D", f'{(D["totalTax"]/D["totalGross"]*100 if D["totalGross"]>0 else 0):.1f}%')}
      </tr>
    </table>
    '''
    st.markdown('<div class="mz-section"><h2>📊 戦略比較表</h2>', unsafe_allow_html=True)
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    cand = best.get("_candidate") or {}
    bandA = build_pension_component_monthly(cand, input_, public_pension_annual, 60, 65)
    bandB = build_pension_component_monthly(cand, input_, public_pension_annual, 65, int(input_["endAge"]))

    def pension_label(prefix: str, band: Dict[str, float]) -> str:
        parts=[]
        if band["idecoM"]>1e-5: parts.append(f"iDeCo年金{_num1(band['idecoM'])}万円")
        if band["dcM"]>1e-5: parts.append(f"企業型DC年金{_num1(band['dcM'])}万円")
        if band["publicM"]>1e-5: parts.append(f"公的年金{_num1(band['publicM'])}万円")
        return f"{prefix}　" + ("＋".join(parts) if parts else "年金なし")

    cashflow_html = f'''
      <h3 style="margin-bottom:15px;">おすすめ戦略（{best["name"]}）の詳細</h3>
      <div class="cashflow-summary">
        <h4>📊 受取サマリー</h4>
'''

    # ① 一時金合計（手取り）
    lumps = best.get("lumpsum") or []
    if lumps:
        lumps_by_age = {}
        for it in lumps:
            lumps_by_age.setdefault(int(it["age"]), []).append(it)
        cashflow_html += '<div class="cashflow-section"><div class="cashflow-section-title">① 一時金合計（手取り）</div>'
        for age in sorted(lumps_by_age.keys()):
            for it in lumps_by_age[age]:
                cashflow_html += textwrap.dedent(f'''
                  <div class="cashflow-line">
                    <span class="label">{age}歳　{it["item"]}</span>
                    <span class="value">{_num(safe_number(it.get("net"),0))}万円</span>
                  </div>
                ''').lstrip()
        total_lumpsum_net = sum(safe_number(it.get("net"),0) for it in lumps)
        cashflow_html += textwrap.dedent(f'''
            <div class="cashflow-line total">
              <span class="label">一時金合計</span>
              <span class="value">{_num(total_lumpsum_net)}万円</span>
            </div>
        ''').lstrip()
        cashflow_html += '</div>'

    # ② 年金（月額概算）
    cashflow_html += textwrap.dedent(f'''
        <div class="cashflow-section">
          <div class="cashflow-section-title">② 年金（月額概算）</div>
          <div class="cashflow-line">
            <span class="label">{pension_label("60〜65歳", bandA)}</span>
            <span class="value">{_num1(bandA["totalM"])}万円/月</span>
          </div>
          <div class="cashflow-line">
            <span class="label">{pension_label("65歳以降", bandB)}</span>
            <span class="value">{_num1(bandB["totalM"])}万円/月</span>
          </div>
        </div>
      </div>
    ''').lstrip()
    st.markdown('<div class="mz-section"><h2>💰 詳細キャッシュフロー</h2>', unsafe_allow_html=True)
    st.markdown(cashflow_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

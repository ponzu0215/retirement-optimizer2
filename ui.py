# ui.py
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import streamlit as st
import streamlit.components.v1 as components
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
            年金は生涯実効税率が最小となる開始年齢を選択します。<br>
            公的年金の受給終了年齢は日本人の平均寿命を考慮し、「90歳」で設定しています。
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

def disable_browser_autofill():
    # Disable browser autofill / saved form suggestions on text inputs (best-effort; browser-dependent).
    components.html(
        """
        <script>
        (function() {
          const setAttrs = () => {
            const inputs = window.parent.document.querySelectorAll('input[type="text"], input[type="number"], input');
            inputs.forEach((el) => {
              try {
                el.setAttribute('autocomplete', 'off');
                el.setAttribute('autocapitalize', 'off');
                el.setAttribute('autocorrect', 'off');
                el.setAttribute('spellcheck', 'false');
              } catch (e) {}
            });
          };
          setAttrs();
          setTimeout(setAttrs, 250);
          setTimeout(setAttrs, 1000);
        })();
        </script>
        """,
        height=0,
        width=0,
    )

def render_shell_end():
    st.markdown("</div></div>", unsafe_allow_html=True)

def _num(x: Any) -> str:
    try: return f"{round(float(x)):,}"
    except Exception: return "0"

def _num1(x: Any) -> str:
    try: return f"{float(x):.1f}"
    except Exception: return "0.0"

def _parse_int(x: Any) -> int:
    try:
        s = "" if x is None else str(x).strip()
        if s == "":
            return 0
        return int(float(s))
    except Exception:
        return 0

def _parse_float(x: Any) -> float:
    try:
        s = "" if x is None else str(x).strip()
        if s == "":
            return 0.0
        return float(s)
    except Exception:
        return 0.0

def render_input_form(defaults: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    disable_browser_autofill()
    with st.form("simulatorForm", clear_on_submit=False):
        st.markdown('<div class="mz-section"><h2>👤 基本情報</h2>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)

        # 退職金受取年齢の初期値制御（自動入力＋上書き可）
        # ・初期値：退職予定年齢（ただし退職予定年齢が60超なら60）
        # ・ユーザーが手入力で変更した場合は、その後は自動で上書きしない
        _ret_ss = str(st.session_state.get("retirementAge", defaults.get("retirementAge", ""))).strip()
        _ret_i = _parse_int(_ret_ss)
        _desired_auto = "" if _ret_i <= 0 else str(60 if _ret_i > 60 else _ret_i)
        _sev_ss = str(st.session_state.get("severanceReceiveAge", defaults.get("severanceReceiveAge", ""))).strip()
        if "_sev_auto" not in st.session_state:
            st.session_state["_sev_auto"] = (_sev_ss == "" or _sev_ss == _desired_auto)
        _last_ret = str(st.session_state.get("_last_retirementAge", "")).strip()
        if _ret_ss != _last_ret and st.session_state.get("_sev_auto", False):
            st.session_state["severanceReceiveAge"] = _desired_auto
            st.session_state["_last_sev_auto_value"] = _desired_auto
        st.session_state["_last_retirementAge"] = _ret_ss

        with c1:
            currentAge = st.text_input("現在の年齢", value=str(defaults.get("currentAge", "")), key="currentAge")
        with c2:
            joinAge = st.text_input("入社年齢", value=str(defaults.get("joinAge", "")), key="joinAge")
        with c3:
            retirementAge = st.text_input("退職予定年齢", value=str(defaults.get("retirementAge", "")), key="retirementAge")
        with c4:
            severanceReceiveAge = st.text_input("退職金受取年齢", value=str(defaults.get("severanceReceiveAge", "")), key="severanceReceiveAge")

        # 入力後に「手入力で上書きされたか」を判定（自動値と異なれば以後自動更新しない）
        _auto_val = str(st.session_state.get("_last_sev_auto_value", _desired_auto)).strip()
        _cur_sev = str(st.session_state.get("severanceReceiveAge", "")).strip()
        if _cur_sev != "" and _auto_val != "" and _cur_sev != _auto_val:
            st.session_state["_sev_auto"] = False
        elif _cur_sev == _auto_val and _auto_val != "":
            st.session_state["_sev_auto"] = True

    
        st.markdown('<div class="mz-section"><h2>💼 退職金情報</h2>', unsafe_allow_html=True)
        severancePay = st.text_input("退職金見込額（万円）", value=str(defaults.get("severancePay", "")), key="severancePay")
    
        st.markdown('<div class="mz-section"><h2>🏢 企業型DC（確定拠出年金）</h2>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            dcCurrentBalance = st.text_input("現在の評価額（万円）", value=str(defaults.get("dcCurrentBalance", "")), key="dcCurrentBalance")
        with c2:
            dcMonthlyContribution = st.text_input("月次拠出額（万円）", value=str(defaults.get("dcMonthlyContribution", "")), key="dcMonthlyContribution")
        dcReturnRate_pct = st.text_input(
            "想定年利率（%）",
            value=("" if str(defaults.get("dcReturnRate", "")).strip() == "" else str(float(defaults.get("dcReturnRate", 0.0)) * 100.0)),
            key="dcReturnRate_pct",
        )
    
        st.markdown('<div class="mz-section"><h2>🏦 iDeCo（個人型確定拠出年金）</h2>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            idecoStartAge = st.text_input("加入開始年齢 ", value=str(defaults.get("idecoStartAge", "")), key="idecoStartAge")
        with c2:
            idecoCurrentBalance = st.text_input("現在の評価額（万円） ", value=str(defaults.get("idecoCurrentBalance", "")), key="idecoCurrentBalance")
        with c3:
            idecoMonthlyContribution = st.text_input("月次拠出額（万円） ", value=str(defaults.get("idecoMonthlyContribution", "")), key="idecoMonthlyContribution")
        idecoReturnRate_pct = st.text_input(
            "想定年利率（%） ",
            value=("" if str(defaults.get("idecoReturnRate", "")).strip() == "" else str(float(defaults.get("idecoReturnRate", 0.0)) * 100.0)),
            key="idecoReturnRate_pct",
        )
    
        st.markdown('<div class="mz-section"><h2>💵 給与・年金情報</h2>', unsafe_allow_html=True)
        c1 = st.columns(1)[0]
        with c1:
            st.markdown(
                '''
                <div class="avg-salary-label">
                  <span>平均標準報酬月額（万円）</span>
                  <details class="avg-salary-details">
                    <summary class="avg-salary-tooltip">平均標準報酬月額って？</summary>
                    <div class="avg-salary-tipbox">
                      <div>入社～退職までの平均年収による平均標準報酬月額の概算</div>
                      <div>・年収400万円：約35万円</div>
                      <div>・年収500万円：約44万円</div>
                      <div>・年収600万円：約53万円</div>
                      <div>・年収700万円：約60万円</div>
                      <div>・年収800万円以上：約65万円</div>
                    </div>
                  </details>
                </div>
                ''',
                unsafe_allow_html=True,
            )
            avgSalary = st.text_input(
                "",
                value=str(defaults.get("avgSalary", "")),
                key="avgSalary",
                label_visibility="collapsed",
            )
        pensionExemption = st.selectbox(
            "60歳未満退職時の国民年金保険料免除",
            options=["免除なし（全額納付）", "免除あり（半額換算、iDeCoの拠出不可）"],
            index=1 if defaults.get("pensionExemption", False) else 0,
            key="pensionExemption",
        )
        idecoContinueContribution = st.selectbox(
            "60歳未満退職時のiDeCo拠出継続",
            options=["60歳までiDeCoを追加拠出する（国民年金免除不可）", "iDeCoの追加拠出なし"],
            index=0 if defaults.get("idecoContinueContribution", False) else 1,
            key="idecoContinueContribution",
        )
        if (pensionExemption == "免除あり（半額換算、iDeCoの拠出不可）") and (idecoContinueContribution == "60歳までiDeCoを追加拠出する（国民年金免除不可）"):
            st.warning("国民年金免除中はiDeCo拠出できないため、「iDeCoの追加拠出なし」に切り替えます。")
            st.session_state["idecoContinueContribution"] = "iDeCoの追加拠出なし"
            idecoContinueContribution = "iDeCoの追加拠出なし"
    
        submitted = st.form_submit_button("💡 最適戦略を計算する", use_container_width=True)

        # UIで非表示にした項目は内部で自動設定して計算に利用します。
        _ret_age_i = _parse_int(retirementAge)
        _join_age_i = _parse_int(joinAge)
        _svc_years_i = (_ret_age_i - _join_age_i) if (_ret_age_i > 0 and _join_age_i > 0) else 0
        _ideco_continue = (idecoContinueContribution == "60歳までiDeCoを追加拠出する（国民年金免除不可）")
        _ideco_end_age_i = (60 if _ideco_continue else _ret_age_i)
        input_internal = {
            "currentAge": _parse_int(currentAge),
            "retirementAge": _ret_age_i,
            "joinAge": _join_age_i,
            "serviceYears": _svc_years_i,
            "severanceReceiveAge": _parse_int(severanceReceiveAge),
            "severancePay": _parse_float(severancePay),

            # 企業型DC：加入開始/拠出終了は自動設定（入社年齢/退職予定年齢。ただし60歳上限）
            "dcStartAge": _join_age_i,
            "dcEndAge": (min(_ret_age_i, 60) if _ret_age_i > 0 else 0),
            "dcCurrentBalance": _parse_float(dcCurrentBalance),
            "dcMonthlyContribution": _parse_float(dcMonthlyContribution),
            "dcReturnRate": _parse_float(dcReturnRate_pct) / 100.0,

            "idecoStartAge": _parse_int(idecoStartAge),
            "idecoEndAge": _ideco_end_age_i,
            "idecoCurrentBalance": _parse_float(idecoCurrentBalance),
            "idecoMonthlyContribution": _parse_float(idecoMonthlyContribution),
            "idecoReturnRate": _parse_float(idecoReturnRate_pct) / 100.0,

            "avgSalary": _parse_float(avgSalary),
            "pensionExemption": (pensionExemption == "免除あり（半額換算、iDeCoの拠出不可）"),
            "idecoContinueContribution": _ideco_continue,
            # 計算終了年齢（受給終了年齢）は90歳固定
            "endAge": 90,
        }
        return submitted, input_internal


def render_results(strategies: List[Dict[str, Any]], best: Dict[str, Any], input_: Dict[str, Any], public_pension_annual: float):

    def _format_strategy_description(desc: str) -> str:
        # 表示のみの整形（計算ロジックには影響しない）
        s = (desc or "").strip()
        if not s:
            return ""
        # 不要な括弧書きを非表示（戦略概要の重複表現を除去）
        s = s.replace("（19年ルール・年齢優先で最適化）", "").replace("（年齢優先で最適化）", "")
        # 余分な空白を整理して1行に
        s = " ".join(s.split())
        # 1行・太字・オレンジで強調（アイコンなし）
        return f'<div style="margin-bottom:20px; font-weight:700; color:#d97706; font-size:18px;">{s}</div>'
    cards_html = ""
    for s in strategies:
        is_rec = (s["code"] == best["code"])
        card_cls = "result-card recommended" if is_rec else "result-card"
        eff = (s["totalTax"]/s["totalGross"]*100) if s["totalGross"]>0 else 0.0
        cards_html += textwrap.dedent(f'''
        <div class="{card_cls}">
          <h3>{s["name"]}{("<span class=\"badge\">おすすめ</span>" if is_rec else "")}</h3>
          {_format_strategy_description(str(s.get("description","")))}
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

    st.markdown('<h2 style="color:#fff; margin-top:10px;">🎯 おすすめ戦略</h2>', unsafe_allow_html=True)
    st.markdown('''
    <div style="background:#fff7ed; border:1px solid #fdba74; padding:12px 14px; border-radius:12px; margin:8px 0 18px 0; color:#7c2d12; line-height:1.6;">
      <div style="font-weight:700;">🔶 受取ルールについて</div>
      <div>本シミュレーションでは、退職所得控除枠の復活などを考慮し、年齢優先・19年ルールに基づいて一時金受取年齢を自動最適化しています。</div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(cards_html, unsafe_allow_html=True)

    by_code = {s["code"]: s for s in strategies}
    A,B,C,D = by_code["A"], by_code["B"], by_code["C"], by_code["D"]
    best_code = best["code"]

    def th(code, label):
        cls = "highlight-orange-header" if code==best_code else ""
        return f'<th class="{cls}">{label}</th>'
    def td(code, content):
        cls = "highlight-orange-cell" if code==best_code else ""
        return f'<td class="{cls}">{content}</td>'

    def _lumpsum_total_net(s: Dict[str, Any]) -> float:
        lumps = s.get("lumpsum") or []
        return float(sum(safe_number(it.get("net"), 0) for it in lumps))

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
        <td>一時金計</td>
        {td("A", _num(_lumpsum_total_net(A))+"万円")}
        {td("B", _num(_lumpsum_total_net(B))+"万円")}
        {td("C", _num(_lumpsum_total_net(C))+"万円")}
        {td("D", _num(_lumpsum_total_net(D))+"万円")}
      </tr>
      <tr>
        <td>60〜65歳 年金手取り月収</td>
        {td("A", f'{float(A.get("monthlyIncome60to65Net",0)):.1f}万円')}
        {td("B", f'{float(B.get("monthlyIncome60to65Net",0)):.1f}万円')}
        {td("C", f'{float(C.get("monthlyIncome60to65Net",0)):.1f}万円')}
        {td("D", f'{float(D.get("monthlyIncome60to65Net",0)):.1f}万円')}
      </tr>
      <tr>
        <td>65歳以降 年金手取り月収</td>
        {td("A", f'{float(A.get("monthlyIncome65plusNet",0)):.1f}万円')}
        {td("B", f'{float(B.get("monthlyIncome65plusNet",0)):.1f}万円')}
        {td("C", f'{float(C.get("monthlyIncome65plusNet",0)):.1f}万円')}
        {td("D", f'{float(D.get("monthlyIncome65plusNet",0)):.1f}万円')}
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
    st.markdown('<div style="height:8px;"></div><h2 style="color:#fff;">📊 戦略比較表</h2>', unsafe_allow_html=True)
    st.markdown(table_html, unsafe_allow_html=True)

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
      <h3 style="margin-bottom:15px; color:#fff;">おすすめ戦略（{best["name"]}）の詳細</h3>
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
    st.markdown(cashflow_html, unsafe_allow_html=True)

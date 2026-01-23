# export_pdf.py
from __future__ import annotations
from typing import Any, Dict, List
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

def _register_japanese_font() -> str:
    try:
        pdfmetrics.registerFont(TTFont("NotoSansJP", "assets/fonts/NotoSansJP-Regular.ttf"))
        return "NotoSansJP"
    except Exception:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
            return "HeiseiKakuGo-W5"
        except Exception:
            return "Helvetica"

def make_pdf_bytes(input_: Dict[str, Any], strategies: List[Dict[str, Any]], best: Dict[str, Any]) -> bytes:
    font_name = _register_japanese_font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setTitle("退職金・年金受取最適化シミュレーション結果")
    c.setFont(font_name, 14)

    y = h - 20*mm
    c.drawString(20*mm, y, "退職金・年金受取最適化シミュレーション結果")
    y -= 8*mm
    c.setFont(font_name, 10)
    c.setFillColor(colors.grey)
    c.drawString(20*mm, y, "（おすすめ戦略＋比較表＋入力条件）")
    c.setFillColor(colors.black)
    y -= 10*mm

    c.setFont(font_name, 12)
    c.drawString(20*mm, y, "入力条件")
    y -= 6*mm
    c.setFont(font_name, 9)

    def row(label: str, value: str):
        nonlocal y
        c.drawString(22*mm, y, label)
        c.drawRightString(w-20*mm, y, value)
        y -= 5*mm

    row("現在の年齢", f"{int(input_['currentAge'])}歳")
    row("退職予定年齢", f"{int(input_['retirementAge'])}歳")
    row("入社年齢", f"{int(input_['joinAge'])}歳")
    row("勤続年数", f"{int(input_['serviceYears'])}年")
    row("退職金見込額", f"{float(input_['severancePay']):,.0f}万円")
    row("企業型DC 現在評価額", f"{float(input_['dcCurrentBalance']):,.0f}万円")
    row("企業型DC 月次拠出額", f"{float(input_['dcMonthlyContribution']):,.1f}万円")
    row("企業型DC 想定年利率", f"{float(input_['dcReturnRate']*100):,.1f}%")
    row("iDeCo 現在評価額", f"{float(input_['idecoCurrentBalance']):,.0f}万円")
    row("iDeCo 月次拠出額", f"{float(input_['idecoMonthlyContribution']):,.1f}万円")
    row("iDeCo 想定年利率", f"{float(input_['idecoReturnRate']*100):,.1f}%")
    row("平均標準報酬月額", f"{float(input_['avgSalary']):,.0f}万円")
    row("国民年金免除", "免除あり（半額換算、iDeCoの拠出不可）" if input_.get("pensionExemption") else "免除なし（全額納付）")
    row("iDeCo拠出継続", "60歳まで追加拠出" if input_.get("idecoContinueContribution") else "追加拠出なし")
    row("計算終了年齢", f"{int(input_['endAge'])}歳")

    y -= 4*mm
    c.setStrokeColor(colors.lightgrey)
    c.line(20*mm, y, w-20*mm, y)
    y -= 10*mm

    c.setFont(font_name, 12)
    c.drawString(20*mm, y, "おすすめ戦略")
    y -= 6*mm

    c.setFont(font_name, 11)
    c.setFillColor(colors.HexColor("#d97706"))
    c.drawString(22*mm, y, str(best.get("name","")))
    c.setFillColor(colors.black)
    y -= 6*mm

    c.setFont(font_name, 9)
    desc = str(best.get("description",""))
    for i in range(0, len(desc), 48):
        c.drawString(22*mm, y, desc[i:i+48])
        y -= 5*mm

    def money(x): return f"{float(x):,.0f}万円"
    eff = (best["totalTax"]/best["totalGross"]*100) if best["totalGross"]>0 else 0.0
    row("総受取額（税引前）", money(best["totalGross"]))
    row("総税負担", money(best["totalTax"]))
    row("総手取額", money(best["totalNet"]))
    row("実効税率", f"{eff:.1f}%")

    y -= 6*mm
    c.setFont(font_name, 12)
    c.drawString(20*mm, y, "戦略比較表")
    y -= 6*mm

    headers = ["項目", "戦略A", "戦略B", "戦略C", "戦略D"]
    col_w = [35*mm, 32*mm, 32*mm, 32*mm, 32*mm]
    x0 = 20*mm
    codes = {"A":1,"B":2,"C":3,"D":4}
    best_col = codes.get(best.get("code",""), None)

    def draw_row(y, cells, header=False):
        x = x0
        hgt = 6*mm
        for j, txt in enumerate(cells, start=1):
            wj = col_w[j-1]
            hi = (best_col == j) and (j != 1)
            if header:
                fill = colors.HexColor("#f9f9f9") if not hi else colors.HexColor("#f59e0b")
                c.setFillColor(fill)
                c.rect(x, y-hgt, wj, hgt, fill=1, stroke=0)
                c.setFillColor(colors.HexColor("#667eea") if not hi else colors.white)
            else:
                fill = colors.white if not hi else colors.HexColor("#fef3c7")
                c.setFillColor(fill)
                c.rect(x, y-hgt, wj, hgt, fill=1, stroke=0)
                c.setFillColor(colors.black)
            c.setFont(font_name, 9)
            c.drawString(x+2*mm, y-4.5*mm, str(txt))
            x += wj
        c.setStrokeColor(colors.lightgrey)
        c.line(x0, y-hgt, x0+sum(col_w), y-hgt)
        return y - hgt

    y = draw_row(y, headers, header=True)

    A,B,C,D = strategies
    def eff_rate(s): return (s["totalTax"]/s["totalGross"]*100) if s["totalGross"]>0 else 0.0
    rows = [
        ("総手取額", money(A["totalNet"]), money(B["totalNet"]), money(C["totalNet"]), money(D["totalNet"])),
        ("総税負担", money(A["totalTax"]), money(B["totalTax"]), money(C["totalTax"]), money(D["totalTax"])),
        ("実効税率", f"{eff_rate(A):.1f}%", f"{eff_rate(B):.1f}%", f"{eff_rate(C):.1f}%", f"{eff_rate(D):.1f}%"),
    ]
    for r in rows:
        if y < 25*mm:
            c.showPage()
            c.setFont(font_name, 10)
            y = h - 20*mm
        y = draw_row(y, r, header=False)

    c.showPage()
    c.save()
    return buf.getvalue()

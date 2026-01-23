# core.py
# Port of "退職金・年金受取最適化シミュレーター v4.4" JavaScript logic to Python.
# IMPORTANT: Do not change formulas/branches/constants/rounding/search logic.
# Mapping comments keep JS function names and intent.

from __future__ import annotations
from typing import Any, Dict, List, Optional
import math

Number = float

def safe_number(value: Any, default_value: Number = 0) -> Number:
    # JS: safeNumber(value, defaultValue=0)
    try:
        if value is None:
            return default_value
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default_value
        return x
    except Exception:
        return default_value

def calculate_retirement_deduction(years: Number) -> Number:
    # JS: calculateRetirementDeduction(years)
    if years <= 20:
        return max(40 * years, 80)
    return 800 + 70 * (years - 20)

def calculate_future_value(current_balance: Number, monthly_contribution: Number, annual_rate: Number,
                           current_age: int, target_age: int, contribution_end_age: int) -> Number:
    # JS: calculateFutureValue(currentBalance, monthlyContribution, annualRate, currentAge, targetAge, contributionEndAge)
    balance = safe_number(current_balance, 0.0)
    monthly_rate = safe_number(annual_rate, 0.0) / 12.0
    for age in range(int(current_age), int(target_age)):
        for _ in range(12):
            balance = balance * (1 + monthly_rate)
            if age < int(contribution_end_age):
                balance += safe_number(monthly_contribution, 0.0)
    return balance

def calculate_public_pension(avg_salary: Number, years_of_service: int, exemption: bool, retirement_age: int) -> Number:
    # JS: calculatePublicPension(avgSalary, yearsOfService, exemption, retirementAge)
    months_of_service = years_of_service * 12
    employee_pension = safe_number(avg_salary, 0.0) * 0.005481 * months_of_service
    full_basic_pension = 81.6
    basic_years = years_of_service
    if exemption and retirement_age < 60:
        exemption_years = 60 - retirement_age
        basic_years += exemption_years * 0.5
    elif (not exemption) and retirement_age < 60:
        basic_years += (60 - retirement_age)
    basic_pension = full_basic_pension * basic_years / 40
    return employee_pension + basic_pension

def calculate_income_tax(income: Number) -> Number:
    # JS: calculateIncomeTax(income) (復興税込 2.1%上乗せ)
    if income <= 0:
        return 0.0
    income_yen = income * 10000
    if income_yen <= 1949000:
        tax = income_yen * 0.05
    elif income_yen <= 3299000:
        tax = income_yen * 0.10 - 97500
    elif income_yen <= 6949000:
        tax = income_yen * 0.20 - 427500
    elif income_yen <= 8999000:
        tax = income_yen * 0.23 - 636000
    elif income_yen <= 17999000:
        tax = income_yen * 0.33 - 1536000
    elif income_yen <= 39999000:
        tax = income_yen * 0.40 - 2796000
    else:
        tax = income_yen * 0.45 - 4796000
    return max(0.0, tax * 1.021) / 10000

def calculate_resident_tax_general(income: Number) -> Number:
    # JS: calculateResidentTaxGeneral(income)
    if income <= 0:
        return 0.0
    return income * 0.10 + 0.5

def calculate_resident_tax_retirement(income: Number) -> Number:
    # JS: calculateResidentTaxRetirement(income)
    if income <= 0:
        return 0.0
    return income * 0.10

def calculate_retirement_tax(amount: Number, deduction: Number) -> Number:
    # JS: calculateRetirementTax(amount, deduction)
    if amount <= deduction:
        return 0.0
    taxable_income = (amount - deduction) / 2
    return calculate_income_tax(taxable_income) + calculate_resident_tax_retirement(taxable_income)

def calculate_pension_deduction(total_pension: Number, age: int) -> Number:
    # JS: calculatePensionDeduction(totalPension, age)
    if age >= 65:
        if total_pension <= 330:
            return 110
        elif total_pension <= 410:
            return total_pension * 0.25 + 27.5
        elif total_pension <= 770:
            return total_pension * 0.15 + 68.5
        elif total_pension <= 1000:
            return total_pension * 0.05 + 145.5
        else:
            return 195.5
    else:
        if total_pension <= 130:
            return 60
        elif total_pension <= 410:
            return total_pension * 0.25 + 27.5
        elif total_pension <= 770:
            return total_pension * 0.15 + 68.5
        elif total_pension <= 1000:
            return total_pension * 0.05 + 145.5
        else:
            return 195.5

def calculate_pension_tax(total_yearly_pension: Number, age: int) -> Number:
    # JS: calculatePensionTax(totalYearlyPension, age)
    deduction = calculate_pension_deduction(total_yearly_pension, age)
    taxable_income = max(0.0, total_yearly_pension - deduction - 48)
    if taxable_income <= 0:
        return 0.0
    return calculate_income_tax(taxable_income) + calculate_resident_tax_general(taxable_income)

def calculate_pmt(principal: Number, annual_rate: Number, years: int) -> Number:
    # JS: calculatePMT(principal, annualRate, years)
    if annual_rate == 0:
        return principal / years
    r = annual_rate
    n = years
    power = (1 + r) ** n
    return principal * r * power / (power - 1)

def merge_intervals(intervals: List[Dict[str, Number]]) -> List[Dict[str, Number]]:
    # JS: mergeIntervals(intervals)
    if not intervals:
        return []
    sorted_int = []
    for i in intervals:
        s = min(i["startAge"], i["endAge"])
        e = max(i["startAge"], i["endAge"])
        if e > s:
            sorted_int.append({"s": s, "e": e})
    sorted_int.sort(key=lambda x: x["s"])
    merged = [sorted_int[0]]
    for cur in sorted_int[1:]:
        last = merged[-1]
        if cur["s"] <= last["e"]:
            last["e"] = max(last["e"], cur["e"])
        else:
            merged.append(cur)
    return merged

def union_length_years(intervals: List[Dict[str, Number]]) -> Number:
    # JS: unionLengthYears(intervals)
    merged = merge_intervals(intervals)
    return sum((it["e"] - it["s"]) for it in merged)

def overlap_length_years(intervals_a: List[Dict[str, Number]], intervals_b: List[Dict[str, Number]]) -> Number:
    # JS: overlapLengthYears(intervalsA, intervalsB)
    A = merge_intervals(intervals_a)
    B = merge_intervals(intervals_b)
    i = 0
    j = 0
    overlap = 0.0
    while i < len(A) and j < len(B):
        s = max(A[i]["s"], B[j]["s"])
        e = min(A[i]["e"], B[j]["e"])
        if e > s:
            overlap += (e - s)
        if A[i]["e"] < B[j]["e"]:
            i += 1
        else:
            j += 1
    return overlap

def retirement_rule_threshold_years(previous_event: Dict[str, Any], current_event: Dict[str, Any]) -> int:
    # New rule (2026/1): threshold depends on kind and order.
    prev_kind = previous_event.get("kind")
    cur_kind = current_event.get("kind")
    if prev_kind in ("ideco", "dc") and cur_kind == "severance":
        return 10
    if prev_kind == "severance" and cur_kind in ("ideco", "dc"):
        return 20
    return 20


def adjusted_deduction_with_19_year_rule(current_event: Dict[str, Any], previous_event: Optional[Dict[str, Any]]) -> Number:
    # JS: adjustedDeductionWith19YearRule(currentEvent, previousEvent)
    base_years = union_length_years(current_event["periods"])
    base_deduction = calculate_retirement_deduction(base_years)
    if not previous_event:
        return base_deduction
    diff = current_event["age"] - previous_event["age"]
    threshold = retirement_rule_threshold_years(previous_event, current_event)
    if diff >= threshold:
        return base_deduction
    overlap_years = overlap_length_years(previous_event["periods"], current_event["periods"])
    overlap_deduction = calculate_retirement_deduction(overlap_years)
    return max(0.0, base_deduction - overlap_deduction)

def build_lump_events(input_: Dict[str, Any], years_of_service: int, options: Dict[str, Any]) -> List[Dict[str, Any]]:
    # JS: buildLumpEvents(input, yearsOfService, options)
    events: List[Dict[str, Any]] = []
    severance_age = int(input_.get("severanceReceiveAge", input_["retirementAge"]))
    events.append({
        "kind": "severance",
        "age": severance_age,
        "items": [{"item": "退職一時金", "age": severance_age, "amount": safe_number(input_["severancePay"], 0.0)}],
        "amount": safe_number(input_["severancePay"], 0.0),
        "periods": [{"startAge": severance_age - years_of_service, "endAge": severance_age}]
    })
    if options.get("dcMode") == "lump":
        age = int(options["dcLumpAge"])
        amount = safe_number(options.get("dcLumpAmount"), 0.0)
        events.append({
            "kind": "dc",
            "age": age,
            "items": [{"item": "企業型DC一時金", "age": age, "amount": amount}],
            "amount": amount,
            "periods": [{"startAge": int(input_["dcStartAge"]), "endAge": int(input_["dcEndAge"])}]
        })
    if options.get("idecoMode") == "lump":
        age = int(options["idecoLumpAge"])
        amount = safe_number(options.get("idecoLumpAmount"), 0.0)
        events.append({
            "kind": "ideco",
            "age": age,
            "items": [{"item": "iDeCo一時金", "age": age, "amount": amount}],
            "amount": amount,
            "periods": [{"startAge": int(input_["idecoStartAge"]), "endAge": int(input_["idecoEndAge"])}]
        })
    m: Dict[int, Dict[str, Any]] = {}
    for ev in events:
        key = int(ev["age"])
        if key not in m:
            m[key] = {"age": key, "amount": 0.0, "periods": [], "items": []}
        agg = m[key]
        agg["amount"] += safe_number(ev["amount"], 0.0)
        agg["periods"].extend(ev["periods"])
        agg["items"].extend(ev["items"])
    out = list(m.values())
    out.sort(key=lambda x: x["age"])
    return out

def calc_pension_totals(input_: Dict[str, Any], public_pension_annual: Number, options: Dict[str, Any]) -> Dict[str, Number]:
    # JS: calcPensionTotals(input, publicPensionAnnual, options)
    end_age = int(input_["endAge"])
    total_gross = 0.0
    total_tax = 0.0
    for age in range(60, end_age):
        yearly = 0.0
        if age >= 65:
            yearly += public_pension_annual
        if options.get("dcMode") == "pension" and age >= int(options["dcPensionStartAge"]):
            yearly += safe_number(options.get("dcPensionAnnual"), 0.0)
        if options.get("idecoMode") == "pension" and age >= int(options["idecoPensionStartAge"]):
            yearly += safe_number(options.get("idecoPensionAnnual"), 0.0)
        if yearly <= 0:
            continue
        total_gross += yearly
        total_tax += calculate_pension_tax(yearly, age)
    return {"totalGross": total_gross, "totalTax": total_tax, "totalNet": total_gross - total_tax}

def evaluate_candidate(input_: Dict[str, Any], public_pension_annual: Number, years_of_service: int,
                       candidate: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    # JS: evaluateCandidate(...)
    dc_lump_amount = 0.0
    if candidate.get("dcMode") == "lump":
        dc_lump_amount = calculate_future_value(
            input_["dcCurrentBalance"], input_["dcMonthlyContribution"], input_["dcReturnRate"],
            int(input_["currentAge"]), int(candidate["dcLumpAge"]), int(input_["dcEndAge"])
        )
    ideco_lump_amount = 0.0
    if candidate.get("idecoMode") == "lump":
        ideco_lump_amount = calculate_future_value(
            input_["idecoCurrentBalance"], input_["idecoMonthlyContribution"], input_["idecoReturnRate"],
            int(input_["currentAge"]), int(candidate["idecoLumpAge"]), int(input_["idecoEndAge"])
        )
    dc_pension_annual = 0.0
    if candidate.get("dcMode") == "pension":
        bal = calculate_future_value(
            input_["dcCurrentBalance"], input_["dcMonthlyContribution"], input_["dcReturnRate"],
            int(input_["currentAge"]), int(candidate["dcPensionStartAge"]), int(input_["dcEndAge"])
        )
        years = max(1, int(input_["endAge"]) - int(candidate["dcPensionStartAge"]))
        dc_pension_annual = calculate_pmt(bal, input_["dcReturnRate"], years)
    ideco_pension_annual = 0.0
    if candidate.get("idecoMode") == "pension":
        bal = calculate_future_value(
            input_["idecoCurrentBalance"], input_["idecoMonthlyContribution"], input_["idecoReturnRate"],
            int(input_["currentAge"]), int(candidate["idecoPensionStartAge"]), int(input_["idecoEndAge"])
        )
        years = max(1, int(input_["endAge"]) - int(candidate["idecoPensionStartAge"]))
        ideco_pension_annual = calculate_pmt(bal, input_["idecoReturnRate"], years)
    options = {
        "dcMode": candidate.get("dcMode"),
        "idecoMode": candidate.get("idecoMode"),
        "dcLumpAge": candidate.get("dcLumpAge"),
        "idecoLumpAge": candidate.get("idecoLumpAge"),
        "dcLumpAmount": dc_lump_amount,
        "idecoLumpAmount": ideco_lump_amount,
        "dcPensionStartAge": candidate.get("dcPensionStartAge"),
        "idecoPensionStartAge": candidate.get("idecoPensionStartAge"),
        "dcPensionAnnual": dc_pension_annual,
        "idecoPensionAnnual": ideco_pension_annual,
    }
    lump_events = build_lump_events(input_, years_of_service, options)
    total_lump_gross = 0.0
    total_lump_tax = 0.0
    lumpsum_breakdown: List[Dict[str, Any]] = []
    prev = None
    for ev in lump_events:
        deduction = adjusted_deduction_with_19_year_rule(ev, prev)
        tax = calculate_retirement_tax(ev["amount"], deduction)
        for item in ev["items"]:
            ratio = (item["amount"] / ev["amount"]) if ev["amount"] > 0 else 0.0
            item_tax = tax * ratio
            item_net = item["amount"] - item_tax
            lumpsum_breakdown.append({"item": item["item"], "age": int(item["age"]), "amount": item["amount"], "tax": item_tax, "net": item_net})
        total_lump_gross += ev["amount"]
        total_lump_tax += tax
        prev = ev
    pension_totals = calc_pension_totals(input_, public_pension_annual, options)
    total_gross = total_lump_gross + pension_totals["totalGross"]
    total_tax = total_lump_tax + pension_totals["totalTax"]
    total_net = total_gross - total_tax

    def band(start_age: int, end_age: int):
        s = max(0, int(start_age))
        e = max(s, min(int(end_age), int(input_["endAge"])))
        years = e - s
        if years <= 0:
            return {"grossMonthly": 0.0, "netMonthly": 0.0}
        gross_sum = 0.0
        tax_sum = 0.0
        for age in range(s, e):
            yearly = 0.0
            if age >= 65:
                yearly += public_pension_annual
            if candidate.get("dcMode") == "pension" and age >= int(candidate["dcPensionStartAge"]):
                yearly += dc_pension_annual
            if candidate.get("idecoMode") == "pension" and age >= int(candidate["idecoPensionStartAge"]):
                yearly += ideco_pension_annual
            gross_sum += yearly
            tax_sum += calculate_pension_tax(yearly, age) if yearly > 0 else 0.0
        return {"grossMonthly": gross_sum/(years*12), "netMonthly": (gross_sum-tax_sum)/(years*12)}

    b60 = band(60, 65)
    b65 = band(65, int(input_["endAge"]))

    strategy = {
        "name": meta["name"],
        "code": meta["code"],
        "description": meta["describe"](candidate, input_),
        "lumpsum": lumpsum_breakdown,
        "totalGross": total_gross,
        "totalTax": total_tax,
        "totalNet": total_net,
        "monthlyIncome60to65Gross": b60["grossMonthly"],
        "monthlyIncome60to65Net": b60["netMonthly"],
        "monthlyIncome65plusGross": b65["grossMonthly"],
        "monthlyIncome65plusNet": b65["netMonthly"],
        "monthlyIncome60to65": b60["grossMonthly"],
        "monthlyIncome65plus": b65["grossMonthly"],
        "_candidate": candidate,
    }
    return {"strategy": strategy, "options": options}

def optimize_strategy(input_: Dict[str, Any], public_pension_annual: Number, years_of_service: int,
                      pattern: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    # JS: optimizeStrategy(...)
    max_receive_age = 75
    retire_age = int(input_["retirementAge"])
    sev_age = int(input_.get("severanceReceiveAge", retire_age))
    max_lump_age = min(max_receive_age, int(input_["endAge"]))

    if sev_age <= 54:
        fixed_age = sev_age + 20
        lump_age = max(60, min(fixed_age, max_lump_age))
        dc_lump_ages = [lump_age]
        ideco_lump_ages = [lump_age]
    else:
        dc_lump_ages = [60]
        ideco_lump_ages = [60]

    plus20_age = sev_age + 20
    can_plus20 = (plus20_age >= 60 and plus20_age <= max_lump_age)

    pension_start_ages = [60]

    best_net_seen = float("-inf")
    best_eff_seen = float("inf")
    best = None

    def eff(s): return (s["totalTax"]/s["totalGross"]) if s["totalGross"]>0 else 1.0
    def guard(res):
        NET_TOL = 0.001
        TAX_TOL_PT = 0.002
        return (res["strategy"]["totalNet"] >= best_net_seen*(1-NET_TOL)) and (eff(res["strategy"]) <= best_eff_seen + TAX_TOL_PT)

    def priority_key(res):
        ages=[]
        o=res["options"]
        if o.get("dcMode")=="lump": ages.append(int(o["dcLumpAge"]))
        if o.get("idecoMode")=="lump": ages.append(int(o["idecoLumpAge"]))
        if o.get("dcMode")=="pension": ages.append(int(o["dcPensionStartAge"]))
        if o.get("idecoMode")=="pension": ages.append(int(o["idecoPensionStartAge"]))
        return {"maxAge": max(ages) if ages else 999, "sumAge": sum(ages)}

    def better(new_res, best_res):
        if best_res is None:
            return True
        n_ok = guard(new_res)
        b_ok = guard(best_res)
        if n_ok != b_ok:
            return n_ok
        nn = new_res["strategy"]["totalNet"]
        bn = best_res["strategy"]["totalNet"]
        ne = eff(new_res["strategy"])
        be = eff(best_res["strategy"])
        if sev_age <= 59:
            if abs(ne-be)>1e-5: return ne < be
            if abs(nn-bn)>1e-5: return nn > bn
        else:
            if abs(nn-bn)>1e-5: return nn > bn
            if abs(ne-be)>1e-5: return ne < be
        A=priority_key(new_res); B=priority_key(best_res)
        if A["maxAge"]!=B["maxAge"]: return A["maxAge"] < B["maxAge"]
        if A["sumAge"]!=B["sumAge"]: return A["sumAge"] < B["sumAge"]
        return False

    def update(res):
        nonlocal best_net_seen, best_eff_seen, best
        best_net_seen = max(best_net_seen, res["strategy"]["totalNet"])
        best_eff_seen = min(best_eff_seen, eff(res["strategy"]))
        if better(res, best):
            best = res

    if pattern=="A":
        dc_candidates = ([plus20_age] + dc_lump_ages) if can_plus20 else list(dc_lump_ages)
        ideco_candidates = ([plus20_age] + ideco_lump_ages) if can_plus20 else list(ideco_lump_ages)
        dc_candidates = sorted(set([a for a in dc_candidates if a >= 60]))
        ideco_candidates = sorted(set([a for a in ideco_candidates if a >= 60]))
        for dc_age in dc_candidates:
            for ideco_age in ideco_candidates:
                cand={"dcMode":"lump","idecoMode":"lump","dcLumpAge":dc_age,"idecoLumpAge":ideco_age,
                      "dcPensionStartAge":None,"idecoPensionStartAge":None}
                update(evaluate_candidate(input_, public_pension_annual, years_of_service, cand, meta))
    elif pattern=="B":
        dc_candidates = ([plus20_age] + dc_lump_ages) if can_plus20 else list(dc_lump_ages)
        dc_candidates = sorted(set([a for a in dc_candidates if a >= 60]))
        for dc_age in dc_candidates:
            for ideco_start in pension_start_ages:
                cand={"dcMode":"lump","idecoMode":"pension","dcLumpAge":dc_age,"idecoLumpAge":None,
                      "dcPensionStartAge":None,"idecoPensionStartAge":ideco_start}
                update(evaluate_candidate(input_, public_pension_annual, years_of_service, cand, meta))
    elif pattern=="C":
        ideco_candidates = ([plus20_age] + ideco_lump_ages) if can_plus20 else list(ideco_lump_ages)
        ideco_candidates = sorted(set([a for a in ideco_candidates if a >= 60]))
        for dc_start in pension_start_ages:
            for ideco_age in ideco_candidates:
                cand={"dcMode":"pension","idecoMode":"lump","dcLumpAge":None,"idecoLumpAge":ideco_age,
                      "dcPensionStartAge":dc_start,"idecoPensionStartAge":None}
                update(evaluate_candidate(input_, public_pension_annual, years_of_service, cand, meta))
    else:
        for dc_start in pension_start_ages:
            for ideco_start in pension_start_ages:
                cand={"dcMode":"pension","idecoMode":"pension","dcLumpAge":None,"idecoLumpAge":None,
                      "dcPensionStartAge":dc_start,"idecoPensionStartAge":ideco_start}
                update(evaluate_candidate(input_, public_pension_annual, years_of_service, cand, meta))

    return best["strategy"] if best else {"name":meta["name"],"code":meta["code"],"description":"計算できませんでした",
                                         "lumpsum":[], "totalGross":0.0,"totalTax":0.0,"totalNet":0.0,
                                         "monthlyIncome60to65Gross":0.0,"monthlyIncome60to65Net":0.0,
                                         "monthlyIncome65plusGross":0.0,"monthlyIncome65plusNet":0.0,
                                         "_candidate":None}

def calculate_strategy_a(input_, public_pension_annual, years_of_service):
    meta={"name":"戦略A：一時金集中型","code":"A",
          "describe":lambda c,_: f"退職金は退職時。DCは{c['dcLumpAge']}歳、iDeCoは{c['idecoLumpAge']}歳に一時金受取（19年ルール・年齢優先で最適化）"}
    return optimize_strategy(input_, public_pension_annual, years_of_service, "A", meta)

def calculate_strategy_b(input_, public_pension_annual, years_of_service):
    meta={"name":"戦略B：分散型①","code":"B",
          "describe":lambda c,_: f"退職金は退職時。DCは{c['dcLumpAge']}歳に一時金、iDeCoは{c['idecoPensionStartAge']}歳から年金受取（19年ルール・年齢優先で最適化）"}
    return optimize_strategy(input_, public_pension_annual, years_of_service, "B", meta)

def calculate_strategy_c(input_, public_pension_annual, years_of_service):
    meta={"name":"戦略C：分散型②","code":"C",
          "describe":lambda c,_: f"退職金は退職時。DCは{c['dcPensionStartAge']}歳から年金、iDeCoは{c['idecoLumpAge']}歳に一時金受取（19年ルール・年齢優先で最適化）"}
    return optimize_strategy(input_, public_pension_annual, years_of_service, "C", meta)

def calculate_strategy_d(input_, public_pension_annual, years_of_service):
    meta={"name":"戦略D：年金集中型","code":"D",
          "describe":lambda c,_: f"退職金は退職時。DCは{c['dcPensionStartAge']}歳から、iDeCoは{c['idecoPensionStartAge']}歳から年金受取（年齢優先で最適化）"}
    return optimize_strategy(input_, public_pension_annual, years_of_service, "D", meta)

def pick_best_strategy(strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
    best = strategies[0]
    for cur in strategies[1:]:
        cur_eff = (cur["totalTax"]/cur["totalGross"]) if cur["totalGross"]>0 else 1.0
        best_eff = (best["totalTax"]/best["totalGross"]) if best["totalGross"]>0 else 1.0
        if abs(cur_eff-best_eff) > 0.005:
            if cur_eff < best_eff:
                best = cur
        else:
            if cur["totalNet"] > best["totalNet"]:
                best = cur
    return best

def build_pension_component_monthly(candidate: Dict[str, Any], input_: Dict[str, Any], public_pension_annual: float,
                                   start_age: int, end_age: int) -> Dict[str, float]:
    s = max(0, int(start_age))
    e = max(s, min(int(end_age), int(input_["endAge"])))
    years = e - s
    if years <= 0:
        return {"years": 0, "publicM": 0.0, "dcM": 0.0, "idecoM": 0.0, "totalM": 0.0}

    dc_annual = 0.0
    if candidate.get("dcMode") == "pension":
        bal = calculate_future_value(input_["dcCurrentBalance"], input_["dcMonthlyContribution"], input_["dcReturnRate"],
                                     int(input_["currentAge"]), int(candidate["dcPensionStartAge"]), int(input_["dcEndAge"]))
        yrs = max(1, int(input_["endAge"]) - int(candidate["dcPensionStartAge"]))
        dc_annual = calculate_pmt(bal, input_["dcReturnRate"], yrs)

    ideco_annual = 0.0
    if candidate.get("idecoMode") == "pension":
        bal = calculate_future_value(input_["idecoCurrentBalance"], input_["idecoMonthlyContribution"], input_["idecoReturnRate"],
                                     int(input_["currentAge"]), int(candidate["idecoPensionStartAge"]), int(input_["idecoEndAge"]))
        yrs = max(1, int(input_["endAge"]) - int(candidate["idecoPensionStartAge"]))
        ideco_annual = calculate_pmt(bal, input_["idecoReturnRate"], yrs)

    public_sum = 0.0; dc_sum = 0.0; ideco_sum = 0.0
    for age in range(s, e):
        if age >= 65:
            public_sum += public_pension_annual
        if candidate.get("dcMode") == "pension" and age >= int(candidate["dcPensionStartAge"]):
            dc_sum += dc_annual
        if candidate.get("idecoMode") == "pension" and age >= int(candidate["idecoPensionStartAge"]):
            ideco_sum += ideco_annual

    public_m = public_sum / (years*12)
    dc_m = dc_sum / (years*12)
    ideco_m = ideco_sum / (years*12)
    total_m = (public_sum+dc_sum+ideco_sum) / (years*12)
    return {"years": years, "publicM": public_m, "dcM": dc_m, "idecoM": ideco_m, "totalM": total_m}

def calculate_all(input_: Dict[str, Any]) -> Dict[str, Any]:
    years_of_service = int(input_["serviceYears"])
    public_pension_annual = calculate_public_pension(input_["avgSalary"], years_of_service, bool(input_["pensionExemption"]), int(input_["retirementAge"]))
    strategies = [
        calculate_strategy_a(input_, public_pension_annual, years_of_service),
        calculate_strategy_b(input_, public_pension_annual, years_of_service),
        calculate_strategy_c(input_, public_pension_annual, years_of_service),
        calculate_strategy_d(input_, public_pension_annual, years_of_service),
    ]
    best = pick_best_strategy(strategies)
    return {"input": input_, "publicPensionAnnual": public_pension_annual, "strategies": strategies, "best": best}

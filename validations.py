# validations.py
from __future__ import annotations
from typing import Any, Dict, List

def validate_input(input_: Dict[str, Any]) -> List[str]:
    errs: List[str] = []

    def _int(key: str) -> int:
        try: return int(input_.get(key, 0))
        except Exception:
            errs.append(f"{key} は整数で入力してください。")
            return 0

    def _float(key: str) -> float:
        try: return float(input_.get(key, 0.0))
        except Exception:
            errs.append(f"{key} は数値で入力してください。")
            return 0.0

    current_age = _int("currentAge")
    retire_age = _int("retirementAge")
    join_age = _int("joinAge")
    service_years = _int("serviceYears")
    end_age = _int("endAge")

    if current_age > retire_age:
        errs.append("現在の年齢は、退職予定年齢以下にしてください。")
    if join_age > retire_age:
        errs.append("入社年齢は、退職予定年齢以下にしてください。")

    if join_age + service_years != retire_age and service_years > 0 and retire_age > 0 and join_age > 0:
        errs.append("整合性チェック：『入社年齢＋勤続年数』が『退職予定年齢』と一致していません（入力値をご確認ください）。")

    dc_start = _int("dcStartAge"); dc_end = _int("dcEndAge")
    ideco_start = _int("idecoStartAge"); ideco_end = _int("idecoEndAge")
    if dc_start > dc_end:
        errs.append("企業型DC：加入開始年齢は、拠出終了年齢以下にしてください。")
    if ideco_start > ideco_end:
        errs.append("iDeCo：加入開始年齢は、拠出終了年齢以下にしてください。")

    if _float("dcReturnRate") < 0:
        errs.append("企業型DC：想定年利率は 0%以上を推奨します。")
    if _float("idecoReturnRate") < 0:
        errs.append("iDeCo：想定年利率は 0%以上を推奨します。")

    if _float("severancePay") < 0:
        errs.append("退職金見込額は 0以上で入力してください。")

    if end_age > 120:
        errs.append("計算終了年齢が大きすぎます（120歳以下を推奨）。")
    if end_age <= 60:
        errs.append("計算終了年齢は 61歳以上を推奨します（60歳以降の年金計算が前提です）。")

    return errs

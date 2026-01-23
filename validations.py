from __future__ import annotations
from typing import Any, Dict, List

def validate_input(input_: Dict[str, Any]) -> List[str]:
    errs: List[str] = []

    def _int(key: str) -> int:
        try:
            v = input_.get(key, 0)
            if v is None:
                return 0
            s = str(v).strip()
            if s == "":
                return 0
            return int(float(s))
        except Exception:
            errs.append(f"{key} は整数で入力してください。")
            return 0

    def _float(key: str) -> float:
        try:
            v = input_.get(key, 0.0)
            if v is None:
                return 0.0
            s = str(v).strip()
            if s == "":
                return 0.0
            return float(s)
        except Exception:
            errs.append(f"{key} は数値で入力してください。")
            return 0.0

    current_age = _int("currentAge")
    retire_age = _int("retirementAge")
    join_age = _int("joinAge")

    # UI上では非表示/自動設定の項目：未入力の場合は内部で補完
    service_years = _int("serviceYears")
    if service_years <= 0 and retire_age > 0 and join_age > 0:
        service_years = retire_age - join_age
        input_["serviceYears"] = service_years

    end_age = _int("endAge")
    if end_age <= 0:
        end_age = 90
        input_["endAge"] = end_age

    # 退職一時金 受取年齢（新規入力）
    sev_receive_age = _int("severanceReceiveAge")
    if sev_receive_age <= 0 and retire_age > 0:
        # 未入力の場合は退職予定年齢を初期値として許容（UI側で60歳上限の初期値セット想定）
        sev_receive_age = retire_age
        input_["severanceReceiveAge"] = sev_receive_age

    if current_age > retire_age and current_age > 0 and retire_age > 0:
        errs.append("現在の年齢は、退職予定年齢以下にしてください。")
    if join_age > retire_age and join_age > 0 and retire_age > 0:
        errs.append("入社年齢は、退職予定年齢以下にしてください。")

    # 退職一時金の受取年齢は、現在年齢以上・退職予定年齢以下・75歳以下（coreのmax_receive_age前提）
    if sev_receive_age > 0:
        if current_age > 0 and sev_receive_age < current_age:
            errs.append("退職金受取年齢は、現在の年齢以上にしてください。")
        if retire_age > 0 and sev_receive_age > retire_age:
            errs.append("退職金受取年齢は、退職予定年齢以下にしてください。")
        if sev_receive_age > 75:
            errs.append("退職金受取年齢は 75歳以下にしてください。")

    # 企業型DC：加入開始/拠出終了はUI上では非表示。未入力の場合は入社年齢/退職予定年齢で補完。
    dc_start = _int("dcStartAge"); dc_end = _int("dcEndAge")
    if dc_start <= 0 and join_age > 0:
        dc_start = join_age
        input_["dcStartAge"] = dc_start
    # 退職予定年齢が60歳以上の場合、DC拠出終了は60歳に自動調整
    if retire_age > 0:
        _dc_end_desired = min(retire_age, 60)
        if dc_end <= 0 or dc_end != _dc_end_desired:
            dc_end = _dc_end_desired
            input_["dcEndAge"] = dc_end

    # iDeCo：拠出終了はUI上では非表示。未入力の場合は退職予定年齢（または追加拠出ありなら60歳）で補完。
    ideco_start = _int("idecoStartAge"); ideco_end = _int("idecoEndAge")

    # 国民年金免除中は iDeCo 追加拠出不可（免除あり × 追加拠出あり を禁止）
    _pension_exemption = input_.get("pensionExemption", False)
    if isinstance(_pension_exemption, str):
        _pension_exemption = (_pension_exemption.strip() != "" and _pension_exemption.strip().lower() not in ("0","false","no","none"))
    _ideco_continue = input_.get("idecoContinueContribution", False)
    if isinstance(_ideco_continue, str):
        _ideco_continue = (_ideco_continue.strip() != "" and _ideco_continue.strip().lower() not in ("0","false","no","none"))
    if _pension_exemption and _ideco_continue:
        errs.append("国民年金免除中はiDeCo拠出できないため、「iDeCo拠出継続（60歳まで追加拠出）」は選べません。")

    if ideco_end <= 0 and retire_age > 0:
        ideco_end = (60 if _ideco_continue else retire_age)
        input_["idecoEndAge"] = ideco_end
    if dc_start > dc_end and dc_start > 0 and dc_end > 0:
        errs.append("企業型DC：加入開始年齢は、拠出終了年齢以下にしてください。")
    if ideco_start > ideco_end and ideco_start > 0 and ideco_end > 0:
        errs.append("iDeCo：加入開始年齢は、拠出終了年齢以下にしてください。")

    if _float("dcReturnRate") < 0:
        errs.append("企業型DC：想定年利率は 0%以上を推奨します。")
    if _float("idecoReturnRate") < 0:
        errs.append("iDeCo：想定年利率は 0%以上を推奨します。")

    if _float("severancePay") < 0:
        errs.append("退職金見込額は 0以上で入力してください。")

    # 計算終了年齢（受給終了年齢）：UIでは固定90。入力があれば過大/過小のみチェック。
    if end_age > 120:
        errs.append("計算終了年齢が大きすぎます（120歳以下を推奨）。")
    if end_age <= 60 and end_age > 0:
        errs.append("計算終了年齢は 61歳以上を推奨します（60歳以降の年金計算が前提です）。")

    return errs

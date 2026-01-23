from __future__ import annotations
from typing import Any, Dict
import json

APP_VERSION = "v4.4-streamlit-port"

def export_input_json(input_internal: Dict[str, Any]) -> str:
    payload = {"app_version": APP_VERSION, "input": input_internal}
    return json.dumps(payload, ensure_ascii=False, indent=2)

def _normalize_input(d: Dict[str, Any]) -> Dict[str, Any]:
    # 互換対応：旧バージョンのJSONに新キーが無い場合は補完する
    # ※UI側でも初期値を入れるが、JSON直読みケースに備える
    if "severanceReceiveAge" not in d or str(d.get("severanceReceiveAge", "")).strip() == "":
        ra = d.get("retirementAge", "")
        if str(ra).strip() != "":
            d["severanceReceiveAge"] = ra
    # 新キー互換：iDeCo拠出継続フラグが無い場合はFalse
    if "idecoContinueContribution" not in d:
        d["idecoContinueContribution"] = False
    return d

def import_input_json(raw: str) -> Dict[str, Any]:
    obj = json.loads(raw)
    if isinstance(obj, dict) and "input" in obj and isinstance(obj["input"], dict):
        return _normalize_input(obj["input"])
    if isinstance(obj, dict):
        return _normalize_input(obj)
    raise ValueError("JSON形式が不正です。")

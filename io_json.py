# io_json.py
from __future__ import annotations
from typing import Any, Dict
import json

APP_VERSION = "v4.4-streamlit-port"

def export_input_json(input_internal: Dict[str, Any]) -> str:
    payload = {"app_version": APP_VERSION, "input": input_internal}
    return json.dumps(payload, ensure_ascii=False, indent=2)

def import_input_json(raw: str) -> Dict[str, Any]:
    obj = json.loads(raw)
    if isinstance(obj, dict) and "input" in obj:
        return obj["input"]
    if isinstance(obj, dict):
        return obj
    raise ValueError("JSON形式が不正です。")

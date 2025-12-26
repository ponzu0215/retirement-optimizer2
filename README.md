# 退職金・年金受取最適化シミュレーター

元HTML「退職金・年金受取最適化シミュレーター」の **計算ロジック（式/分岐/閾値/丸め/探索/税計算）を変更せず**、Streamlit + Python に移植した社内共有用Webアプリです。

## 構成
- `app.py`：Streamlit起動点（タブ/状態管理/JSON入出力/PDF出力）
- `ui.py`：UI描画（戦略カード4枚・比較表・おすすめ詳細）
- `core.py`：**計算ロジック（JS関数と1対1対応）**
- `export_pdf.py`：PDF出力（日本語フォント対応）
- `io_json.py`：入力のJSON保存/復元
- `validations.py`：入力矛盾チェック
- `assets/styles.css`：元HTML CSSの移植（Streamlit用微調整）
- `tests/test_core.py`：簡易テスト

## ローカル実行
```bash
python -m venv .venv
source .venv/bin/activate  # Windowsは .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud
1. このフォルダをそのままGitHubにpush
2. Streamlit Community CloudでRepoを指定
3. Main file：`app.py`
4. requirements：`requirements.txt`

## 社内サーバー例
```bash
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## テスト
```bash
pytest -q
```

## PDFの日本語
`export_pdf.py` は次の順で日本語フォントを利用します：
1. `assets/fonts/NotoSansJP-Regular.ttf` があれば使用
2. 無ければ reportlab の CIDフォント `HeiseiKakuGo-W5` を使用

（必要なら `assets/fonts/` にTTFを配置してください）

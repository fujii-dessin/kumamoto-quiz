# 🐻 熊本ご当地クイズ

Gemini API を使った熊本のご当地クイズアプリ（Streamlit）。
講座のチャットボットのサンプルをベースに作成。

## 動かし方

1. `.streamlit/secrets.toml` に Gemini API キーを書く（Streamlit Community Cloud なら Settings → Secrets）

   ```
   GEMINI_API_KEY = "ここにキー"
   ```

2. 実行

   ```
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```

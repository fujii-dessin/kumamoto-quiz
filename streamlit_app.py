import streamlit as st
import requests

st.title("🐻 熊本ご当地クイズ")
st.write("Gemini に熊本のクイズを出してもらいます。")

# Streamlit の Secrets から API キーを取得
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.info("Streamlit の Secrets に `GEMINI_API_KEY` を設定してください。", icon="🗝️")
else:
    if st.button("問題を出して！"):
        prompt = "熊本県のご当地クイズを1問出してください。"

        api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-3.8-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_api_key,
        }
        data = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        }

        with st.spinner("問題を考え中..."):
            response = requests.post(api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]

        st.markdown(text)

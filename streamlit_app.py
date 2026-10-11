import json
import streamlit as st
import requests

st.title("🐻 熊本ご当地クイズ")
st.write("Gemini が熊本の4択クイズを出します。")

# Streamlit の Secrets から API キーを取得
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.info("Streamlit の Secrets に `GEMINI_API_KEY` を設定してください。", icon="🗝️")
    st.stop()


def make_quiz(level):
    """Gemini にクイズを1問作ってもらう"""
    prompt = f"""あなたは熊本県のご当地クイズの出題者です。
難易度「{level}」で、熊本の地理・歴史・グルメ・方言・観光から4択クイズを1問作ってください。
次の JSON 形式だけを返してください。前後に説明文は書かないでください。
{"question": "問題文", "choices": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"], "answer": 0, "explanation": "解説"}
answer は正解の番号（0〜3）です。"""

    api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-3.8-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": gemini_api_key,
    }
    data = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }
    response = requests.post(api_url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    # ```json 〜 ``` で囲まれて返ってくることがあるので、{ から } までだけ取り出す
    text = text[text.find("{") : text.rfind("}") + 1]
    return json.loads(text)


# 問題・スコアを覚えておく（ボタンを押すたびに画面が再読み込みされるため）
if "quiz" not in st.session_state:
    st.session_state.quiz = None        # いま出ている問題
    st.session_state.qno = 0            # 何問目か
    st.session_state.answered = False   # 回答済みかどうか
    st.session_state.correct = False    # 正解したかどうか
    st.session_state.score = 0          # 正解数
    st.session_state.total = 0          # 回答数

level = st.selectbox("難易度", ("観光客レベル", "県民レベル", "マニアレベル"))

if st.button("問題を出して！"):
    with st.spinner("問題を考え中..."):
        st.session_state.quiz = make_quiz(level)
    st.session_state.qno += 1
    st.session_state.answered = False

quiz = st.session_state.quiz
if quiz:
    st.subheader(f"第{st.session_state.qno}問")
    st.write(quiz["question"])
    # key を問題ごとに変えると、新しい問題で選択がリセットされる
    choice = st.radio(
        "答えを選んでください",
        quiz["choices"],
        index=None,
        key=f"choice_{st.session_state.qno}",
    )

    if not st.session_state.answered:
        if st.button("回答する"):
            if choice is None:
                st.warning("選択肢を選んでください。")
            else:
                st.session_state.answered = True
                st.session_state.total += 1
                st.session_state.correct = quiz["choices"].index(choice) == quiz["answer"]
                if st.session_state.correct:
                    st.session_state.score += 1

    if st.session_state.answered:
        if st.session_state.correct:
            st.success("正解！🎉")
        else:
            st.error(f"残念… 正解は「{quiz['choices'][quiz['answer']]}」でした。")
        st.write(quiz["explanation"])

st.divider()
st.write(f"スコア: **{st.session_state.score} / {st.session_state.total}** 問正解")

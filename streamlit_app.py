import json
import random
import streamlit as st
import requests

st.title("🐻 熊本ご当地クイズ")
st.write("Gemini が熊本の4択クイズを出します。")

# Streamlit の Secrets から API キーを取得
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.info("Streamlit の Secrets に `GEMINI_API_KEY` を設定してください。", icon="🗝️")
    st.stop()


# 出題ジャンル。毎回この中からランダムに1つ選ぶ（同じ問題ばかりにならないように）
GENRES = ["地理", "歴史", "グルメ", "観光地", "祭り・イベント", "自然・温泉", "ゆるキャラ・名産品", "交通・鉄道"]


def make_quiz(asked, bad):
    """Gemini にクイズを1問作ってもらう。asked は出題済みの問題文、bad は間違いだった問題文のリスト"""
    genre = random.choice(GENRES)
    asked_text = "\n".join(f"- {q}" for q in asked) if asked else "（まだありません）"
    bad_text = "\n".join(f"- {q}" for q in bad) if bad else "（まだありません）"
    prompt = f"""あなたは熊本県のご当地クイズの出題者です。
熊本の「{genre}」に関する4択クイズを1問作ってください。
観光で熊本に来た人でも楽しめる、ほどよい難しさにしてください。
Wikipedia や観光サイトに載っているような、広く知られた事実だけを問題にしてください。
自信がない事柄や、熊本以外の県のことは使わないでください。

これまでに出した問題（これらと同じ題材・似た問題は避けてください）:
{asked_text}

人間がチェックして「事実と違う」と判定した問題（これらと似た問題は絶対に出さないでください）:
{bad_text}

次の JSON 形式だけを返してください。前後に説明文は書かないでください。
{{"question": "問題文", "choices": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"], "answer": 0, "explanation": "解説"}}
answer は正解の番号（0〜3）です。"""

    api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-3.5-flash-lite:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": gemini_api_key,
    }
    data = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        # 1.0 に近いほど毎回違う答えになりやすい
        "generationConfig": {"temperature": 1.0},
    }
    response = requests.post(api_url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    # ```json 〜 ``` で囲まれて返ってくることがあるので、{ から } までだけ取り出す
    text = text[text.find("{") : text.rfind("}") + 1]
    quiz = json.loads(text)
    # 形が崩れていたら（選択肢が4つない、正解番号が範囲外など）エラーにして出し直してもらう
    if len(quiz["choices"]) != 4 or not (0 <= int(quiz["answer"]) <= 3):
        raise ValueError("AI の返した問題の形式がおかしい")
    quiz["answer"] = int(quiz["answer"])
    return quiz


# 問題・スコアを覚えておく（ボタンを押すたびに画面が再読み込みされるため）
# 1つずつ「まだ無ければ作る」にしておくと、あとから項目を足しても
# 開きっぱなしの画面でエラーにならない
DEFAULTS = {
    "quiz": None,       # いま出ている問題
    "qno": 0,           # 何問目か
    "answered": False,  # 回答済みかどうか
    "correct": False,   # 正解したかどうか
    "score": 0,         # 正解数
    "total": 0,         # 回答数
    "asked": [],        # これまでに出した問題文
    "bad": [],          # 「おかしい」と報告された問題文
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

if st.button("問題を出して！"):
    try:
        with st.spinner("問題を考え中..."):
            st.session_state.quiz = make_quiz(st.session_state.asked, st.session_state.bad)
        st.session_state.asked.append(st.session_state.quiz["question"])
        st.session_state.qno += 1
        st.session_state.answered = False
    except Exception as e:
        # Gemini が混んでいて時間切れになったり、JSON がうまく読めなかったとき
        st.error("問題を作れませんでした。もう一度「問題を出して！」を押してください。")
        st.caption(f"エラー内容: {e}")

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

    # AI の問題が間違っていることがあるので、人間が指摘できるボタン
    if st.button("🚫 この問題はおかしい"):
        st.session_state.bad.append(quiz["question"])
        if st.session_state.answered:
            # 採点済みならスコアから取り消す
            st.session_state.total -= 1
            if st.session_state.correct:
                st.session_state.score -= 1
        st.session_state.quiz = None
        st.session_state.answered = False
        st.rerun()

if st.session_state.bad:
    st.info(f"おかしいと報告した問題: {len(st.session_state.bad)} 件（次からは似た問題を出さないように AI に伝えています）")

st.divider()
st.write(f"スコア: **{st.session_state.score} / {st.session_state.total}** 問正解")

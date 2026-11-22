# main.py
import streamlit as st

# 全ページ共通の設定（ブラウザのタブ名、画面の横幅など）
st.set_page_config(page_title="おもち アナリティクス", layout="wide")

# ナビゲーション
pg = st.navigation([
    st.Page("views/overview.py", title="概要", default=True),
    st.Page("views/videos.py", title="動画一覧"),
    st.Page("views/analysis.py", title="比較と分析"),
    # st.Page("views/timing.py", title="視聴者の時間帯"), 後で追加したい
])

st.caption("データ元：YouTube Studio のCSV書き出し（2026/11/20時点）")

pg.run()


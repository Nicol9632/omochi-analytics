import streamlit as st

from src.load_data import load_videos

videos = load_videos()

st.header("動画一覧")
st.write("種類やタイトルで絞り込み、列の見出しをクリックして並べ替え")

# ① 絞り込みの操作
col1, col2 = st.columns([1, 2])
with col1:
    kind = st.radio("種類", ["すべて", "ショート", "動画", "配信"], horizontal=True)
with col2:
    keyword = st.text_input("タイトルで検索", placeholder="シチュボ")

# ② 条件に合う行だけ残す
filtered = videos
if kind != "すべて":
    filtered = filtered[filtered["種類"] == kind]
if keyword:
    filtered = filtered[filtered["動画のタイトル"].str.contains(keyword, case=False, regex=False)]

# ③ 表示用の列を作る
table = filtered.assign(
    長さ分=filtered["長さ"] / 60,
    平均視聴時間分=(filtered["総再生時間（単位: 時間）"] * 60 / filtered["視聴回数"]).where(filtered["視聴回数"] > 0),
)[[
    "動画のタイトル", "種類", "動画公開時刻", "長さ分", "視聴回数",
    "平均視聴時間分", "チャンネル登録者", "サムネイルのクリック率 (%)",
]].sort_values("視聴回数", ascending=False)

# ④ 件数と表
st.caption(f"{len(table)}本を表示中（全{len(videos)}本）")
st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    height=600,
    column_config={
        "動画のタイトル": st.column_config.TextColumn("タイトル", width="large"),
        "動画公開時刻": st.column_config.DateColumn("公開日", format="YYYY/MM/DD"),
        "長さ分": st.column_config.NumberColumn("長さ（分）", format="%.1f"),
        "視聴回数": st.column_config.ProgressColumn(
            "視聴回数", format="%d", min_value=0, max_value=int(videos["視聴回数"].max())
        ),
        "平均視聴時間分": st.column_config.NumberColumn("平均視聴時間（分）", format="%.1f"),
        "チャンネル登録者": st.column_config.NumberColumn("登録者増", format="%d"),
        "サムネイルのクリック率 (%)": st.column_config.NumberColumn("クリック率", format="%.1f%%"),
    },
)
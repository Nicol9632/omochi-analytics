import streamlit as st
import pandas as pd
import plotly.express as px

from src.load_data import load_daily,load_videos,load_traffic


daily = load_daily()
videos = load_videos()
traffic = load_traffic()

st.header("概要")
st.write("日別データでチャンネル全体の動きを見る")

# ② 選択肢と日数の対応表（全期間は「絞り込まない」なので None）
PERIODS = {"7日": 7, "28日": 28, "90日": 90, "全期間": None}

label = st.radio("集計期間", list(PERIODS), horizontal=True)
days = PERIODS[label]

# 期間で絞り込み
latest_date = daily["日付"].max()
if days is None:
    filtered = daily
    filtered_videos = videos
else:
    start = latest_date - pd.Timedelta(days=days)
    filtered = daily[daily["日付"] > start]
    filtered_videos = videos[videos["動画公開時刻"] > start]

total_views = filtered["視聴回数"].sum()
average_views = filtered["視聴回数"].mean()

with st.container(horizontal=True):
    st.metric("視聴回数", f"{total_views:,.0f}回", border=True)
    st.metric("1日平均", f"{average_views:,.0f}回", border=True)
    st.metric("公開した本数", f"{len(filtered_videos)}本", border=True)
    st.metric("登録者の増加", f"{filtered['チャンネル登録者'].sum():,.0f}人", border=True)
    
left, right = st.columns([2, 1], border=True)
with left:
    st.subheader("日別の視聴回数")
    fig = px.line(filtered, x="日付", y="視聴回数")
    fig.update_traces(line_color="#B07A1E")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")
with right:
    st.subheader("コンテンツの種類別")
    st.caption("視聴回数の割合（全期間）")
    by_type = videos.groupby("種類", as_index=False)["視聴回数"].sum()
    by_type["割合"] = by_type["視聴回数"] / by_type["視聴回数"].sum() * 100
    by_type = by_type.sort_values("割合", ascending=False)
    for _, row in by_type.iterrows():
        st.write(f"{row['種類']}　**{row['割合']:.0f}%**")
        st.progress(row["割合"] / 100)

left2, right2 = st.columns([1, 1], border=True)
with left2:
    st.subheader("視聴者がどこから来たか")

    # 期間で絞り込む（日別と同じ考え方）
    if days is None:
        filtered_traffic = traffic
    else:
        filtered_traffic = traffic[traffic["日付"] > start]

    # 流入元ごとに合計して、多い順に上位6つ
    by_source = (
        filtered_traffic.groupby("トラフィック ソース", as_index=False)["視聴回数"].sum()
        .sort_values("視聴回数", ascending=False)
        .head(6)
    )
    by_source["割合"] = by_source["視聴回数"] / filtered_traffic["視聴回数"].sum() * 100

    fig3 = px.bar(
        by_source, x="視聴回数", y="トラフィック ソース", orientation="h",
        text=by_source["割合"].map(lambda v: f"{v:.0f}%"),
    )
    fig3.update_traces(marker_color="#B07A1E")
    fig3.update_layout(
        height=280, margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(categoryorder="total ascending", title=None), xaxis_title=None,
    )
    st.plotly_chart(fig3, width="stretch")
with right2:
    st.subheader("よく見られている動画")
    top = filtered_videos.sort_values("視聴回数", ascending=False).head(5)
    st.dataframe(top[["動画のタイトル", "種類", "視聴回数"]], hide_index=True)
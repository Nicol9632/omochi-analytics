from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.load_data import load_comments

ACCENT = "#B07A1E"
EXPERIMENT_FILE = Path("data/raw/experiment.csv")
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]
SLOTS = ["0時", "3時", "6時", "9時", "12時", "15時", "18時", "21時"]

st.header("視聴者の時間帯")
st.write("コメントの時刻と投稿時間の実験から、視聴者が反応しやすい時間を調べる")

# =========================================================
# ① コメントが書かれた時間帯
# =========================================================
with st.container(border=True):
    st.subheader("コメントが書かれた時間帯")

    comments = load_comments()
    if comments is None:
        st.info("コメントのデータがまだありません。`python -m src.fetch_comments` を実行して取得してください。")
    else:
        exclude = st.toggle("公開後48時間のコメントを除く",
                            help="コメントは公開直後に集中するため、除くと「視聴者が自分から見に来る時間」に近づく")
        data = comments
        if exclude:
            hours = (data["commented_at"] - data["published_at"]).dt.total_seconds() / 3600
            data = data[hours > 48]

        # 曜日と3時間ごとの枠に分けて数える
        heat = pd.DataFrame({
            "曜日": data["commented_at"].dt.dayofweek.map(lambda d: WEEKDAYS[d]),
            "時間帯": data["commented_at"].dt.hour.map(lambda h: SLOTS[h // 3]),
        })
        table = (heat.groupby(["曜日", "時間帯"]).size()
                 .unstack(fill_value=0)
                 .reindex(index=WEEKDAYS, columns=SLOTS, fill_value=0))

        fig = px.imshow(table, text_auto=True, aspect="auto",
                        color_continuous_scale=["#F6EFE2", ACCENT, "#5A3C0C"])
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0),
                          xaxis_title=None, yaxis_title=None, coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")

        day, slot = table.stack().idxmax()
        st.caption(f"集計したコメント {len(data):,}件 ／ いちばん多い枠：{day}曜 {slot}台")
        if len(data) < 100:
            st.caption("件数が少ないため参考値です")

# =========================================================
# ② 投稿時間の実験
# =========================================================
with st.container(border=True):
    st.subheader("投稿時間の実験")
    st.caption("ショートの投稿時間を変えて、公開後24・48時間の視聴回数を記録する（数字は各動画のアナリティクスで確認）")

    if EXPERIMENT_FILE.exists():
        log = pd.read_csv(EXPERIMENT_FILE, parse_dates=["公開日"])
    else:
        log = pd.DataFrame({
            "タイトル": pd.Series(dtype="str"),
            "公開日": pd.Series(dtype="datetime64[ns]"),
            "投稿時間帯": pd.Series(dtype="str"),
            "24時間後": pd.Series(dtype="Int64"),
            "48時間後": pd.Series(dtype="Int64"),
        })

    edited = st.data_editor(
        log, num_rows="dynamic", hide_index=True, width="stretch",
        column_config={
            "公開日": st.column_config.DateColumn(format="YYYY/MM/DD"),
            "投稿時間帯": st.column_config.SelectboxColumn(options=["18時台", "21時台", "その他"]),
        },
    )
    if st.button("記録を保存"):
        edited.to_csv(EXPERIMENT_FILE, index=False)
        st.success("保存しました")

    done = edited.dropna(subset=["投稿時間帯", "48時間後"])
    if len(done):
        summary = done.groupby("投稿時間帯").agg(本数=("48時間後", "count"),
                                              平均48時間後=("48時間後", "mean")).round(0)
        st.dataframe(summary)
        if (summary["本数"] < 3).any():
            st.caption("本数が3本未満の時間帯があります。そろうまで判断は保留にしましょう")

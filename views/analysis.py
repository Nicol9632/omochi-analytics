import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.load_data import load_daily, load_videos, load_traffic

ACCENT = "#B07A1E"

daily = load_daily()
videos = load_videos()
traffic = load_traffic()

st.header("比較と分析")
st.write("何が視聴回数や登録者につながっているかを調べる")

# =========================================================
# ① 種類別の比較（1本あたり平均）
# =========================================================
with st.container(border=True):
    st.subheader("種類別の比較（1本あたり平均）")

    METRICS = {
        "視聴回数": "視聴回数",
        "総再生時間（時間）": "総再生時間（単位: 時間）",
        "登録者増": "チャンネル登録者",
    }
    metric_label = st.radio("比べる指標", list(METRICS), horizontal=True)
    col = METRICS[metric_label]

    by_type = videos.groupby("種類").agg(平均=(col, "mean"), 本数=(col, "count")).reset_index()
    fig = px.bar(
        by_type, x="平均", y="種類", orientation="h",
        text=by_type["平均"].map(lambda v: f"{v:,.1f}"),
        custom_data=["本数"],
    )
    fig.update_traces(marker_color=ACCENT,
                      hovertemplate="%{y}：%{x:,.1f}（%{customdata[0]}本）<extra></extra>")
    fig.update_layout(height=220, margin=dict(l=0, r=0, t=10, b=0),
                      xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig, width="stretch")
    st.caption("各動画の全期間の累計を、種類ごとに平均したもの。動画は本数が少ないので参考値")

# =========================================================
# ② 流入元の月別推移
# =========================================================
with st.container(border=True):
    st.subheader("流入元の割合の変化（月別）")

    monthly = traffic.copy()
    monthly["月"] = monthly["日付"].dt.strftime("%Y-%m")

    # 上位4つ以外は「その他」にまとめる
    top4 = traffic.groupby("トラフィック ソース")["視聴回数"].sum().nlargest(4).index
    monthly["流入元"] = monthly["トラフィック ソース"].where(
        monthly["トラフィック ソース"].isin(top4), "その他"
    )
    by_month = monthly.groupby(["月", "流入元"], as_index=False)["視聴回数"].sum()
    by_month["割合"] = by_month["視聴回数"] / by_month.groupby("月")["視聴回数"].transform("sum") * 100

    fig2 = px.bar(
        by_month, x="月", y="割合", color="流入元",
        category_orders={"流入元": list(top4) + ["その他"]},
        color_discrete_sequence=[ACCENT, "#2a78d6", "#1baf7a", "#e87ba4", "#B4B2A9"],
    )
    fig2.update_traces(hovertemplate="%{x}：%{y:.0f}%<extra></extra>")
    fig2.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                       xaxis_title=None, yaxis_title="割合（%）",
                       legend=dict(orientation="h", y=1.12, x=0, title=None))
    st.plotly_chart(fig2, width="stretch")
    st.caption("夏以降ショートフィードの割合が下がり、ブラウジング機能とYouTube検索が増えている")

# =========================================================
# ③ 動画を公開した日としなかった日
# =========================================================
with st.container(border=True):
    st.subheader("動画を公開した日としなかった日")

    posted_days = videos["動画公開時刻"].dt.normalize().unique()
    days_df = daily[daily["視聴回数"] > 0].copy()   # 活動開始前の日を除く
    days_df["公開した日"] = days_df["日付"].isin(posted_days)

    compare = days_df.groupby("公開した日").agg(
        日数=("日付", "count"),
        視聴回数=("視聴回数", "mean"),
        登録者=("チャンネル登録者", "mean"),
    )

    c1, c2 = st.columns(2)
    for column, flag, title in [(c1, True, "公開した日"), (c2, False, "公開しなかった日")]:
        row = compare.loc[flag]
        with column:
            st.metric(f"{title}（{int(row['日数'])}日）", f"{row['視聴回数']:,.0f}回/日", border=True)
            st.caption(f"登録者 {row['登録者']:+.1f}人/日")

    ratio = compare.loc[True, "視聴回数"] / compare.loc[False, "視聴回数"]
    st.write(f"公開した日は、しなかった日の約 **{ratio:.1f}倍** 見られている")
    st.caption("注意：活動初期はほぼ毎日公開していて、視聴回数も多い時期だった。時期の影響も混ざっている")

# =========================================================
# ④ 回帰分析：1日の視聴回数と登録者の増加
# =========================================================
with st.container(border=True):
    st.subheader("回帰分析：視聴回数が増えると登録者は増える？")
    st.caption("1点 = 1日。日別データで「視聴回数」と「その日の登録者の増加」の関係を調べる")

    x = days_df["視聴回数"].to_numpy()
    y = days_df["チャンネル登録者"].to_numpy()

    a, b = np.polyfit(x, y, 1)                 # 傾き a と切片 b を求める
    r2 = np.corrcoef(x, y)[0, 1] ** 2          # 決定係数 R²

    fig4 = px.scatter(days_df, x="視聴回数", y="チャンネル登録者", opacity=0.6,
                      hover_data={"日付": "|%Y/%m/%d"})
    fig4.update_traces(marker=dict(color=ACCENT, size=7))
    xs = np.array([x.min(), x.max()])
    fig4.add_scatter(x=xs, y=a * xs + b, mode="lines", name="回帰直線",
                     line=dict(color="#1E1C18", dash="dash"))
    fig4.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0),
                       xaxis_title="1日の視聴回数", yaxis_title="その日の登録者の増加",
                       showlegend=False)

    left, right = st.columns([2, 1])
    with left:
        st.plotly_chart(fig4, width="stretch")
    with right:
        st.metric("回帰式", f"y = {a:.4f}x {b:+.2f}")
        st.metric("決定係数 R²", f"{r2:.2f}")
        views_input = st.slider("1日の視聴回数", 0, int(x.max()), 1000, step=100)
        st.metric("予測される登録者の増加", f"{a * views_input + b:.1f}人/日")

    st.write(
        f"1日の視聴回数が1,000回増えると、登録者は約 **{a * 1000:.1f}人** 増える傾向。"
        f"R²は {r2:.2f} で、登録者の増減の約{r2 * 100:.0f}%を視聴回数で説明できている"
    )
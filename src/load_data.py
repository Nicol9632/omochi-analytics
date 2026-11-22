import pandas as pd
import streamlit as st

def classify_type(row):
    """1本の動画の種類を決める"""
    if "\n" in row["動画のタイトル"]:
        return "告知"
    if pd.isna(row["動画公開時刻"]):
        return "非公開・メン限"
    if row["長さ"] <= 180:
        return "ショート"
    if row["長さ"] >= 1800:
        return "配信"
    return "動画"

# データを書き出した日（更新したらここだけ変える）
DATA_DATE = "20261121"
RAW = "data/raw"

@st.cache_data
def load_daily():
    """日別の視聴回数と登録者数を、日付でつなげて読み込む"""
    views = pd.read_csv(f"{RAW}/daily_views_all_{DATA_DATE}.csv", parse_dates=["日付"])
    subs = pd.read_csv(f"{RAW}/daily_subscribers_all_{DATA_DATE}.csv", parse_dates=["日付"])
    return views.merge(subs, on="日付", how="inner")


def classify_type(row):
    """1本の動画の種類を決める"""
    if "\n" in row["動画のタイトル"]:
        return "告知"
    if pd.isna(row["動画公開時刻"]):
        return "非公開・メン限"
    if row["長さ"] <= 180:
        return "ショート"
    if row["長さ"] >= 1800:
        return "配信"
    return "動画"


@st.cache_data
def load_videos():
    videos = pd.read_csv(f"{RAW}/videos_all_{DATA_DATE}.csv")

    # ① 1行目の「合計」行を除く
    videos = videos[videos["コンテンツ"] != "合計"].copy()

    # ② 動画IDの前後の空白を消す
    videos["コンテンツ"] = videos["コンテンツ"].str.strip()

    # ③ 「Nov 5, 2026」を日付型にする（空欄はNaTのまま）
    videos["動画公開時刻"] = pd.to_datetime(videos["動画公開時刻"], format="%b %d, %Y")

    # ④ 数字の空欄を0にする
    num_cols = ["視聴回数", "総再生時間（単位: 時間）", "チャンネル登録者", "サムネイルのインプレッション"]
    videos[num_cols] = videos[num_cols].fillna(0)

    # ⑤ 種類の列を足す
    videos["種類"] = videos.apply(classify_type, axis=1)

    # ⑥ 一般公開の動画だけ残す
    videos = videos[~videos["種類"].isin(["告知", "非公開・メン限"])]

    return videos.reset_index(drop=True)


@st.cache_data
def load_traffic():
    """流入元ごとの日別の視聴回数（グラフデータ.csv）を読み込む"""
    return pd.read_csv(f"{RAW}/traffic_daily_all_{DATA_DATE}.csv", parse_dates=["日付"])

def _latest(pattern):
    """data/raw の中で、名前が pattern に合う最新のファイルを返す（なければ None）"""
    files = sorted(Path(RAW).glob(pattern))
    return files[-1] if files else None


@st.cache_data
def load_comments():
    """コメントの書き込み日時（日本時間）に、動画の公開日時をくっつけて返す"""
    c_file, v_file = _latest("comments_*.csv"), _latest("videos_published_*.csv")
    if c_file is None or v_file is None:
        return None
    comments = pd.read_csv(c_file)
    published = pd.read_csv(v_file)
    comments["commented_at"] = pd.to_datetime(comments["commented_at"], utc=True).dt.tz_convert("Asia/Tokyo")
    published["published_at"] = pd.to_datetime(published["published_at"], utc=True).dt.tz_convert("Asia/Tokyo")
    return comments.merge(published, on="video_id", how="left")
"""Small analytical helpers shared by dashboard sections."""
import pandas as pd

ENGAGEMENT_PARTS = ["Likes", "Comments", "Shares", "Saves"]


def filter_data(df, date_range=None, post_types=None, campaigns=None, hashtags=None):
    out = df.copy()
    if date_range and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        out = out[out["Post Date"].between(start, end)]
    if post_types:
        out = out[out["Post Type"].isin(post_types)]
    if campaigns and "Campaign Type" in out:
        out = out[out["Campaign Type"].isin(campaigns)]
    if hashtags and "_Hashtags" in out:
        selected = {h.lower().lstrip("#") for h in hashtags}
        out = out[out["_Hashtags"].apply(lambda hs: bool(selected.intersection(h.lstrip("#") for h in hs)))]
    return out


def kpis(df):
    return {"posts": len(df), "likes": df["Likes"].sum(min_count=1), "comments": df["Comments"].sum(min_count=1),
            "reach": df["Reach"].sum(min_count=1), "avg_er": df["Engagement Rate"].mean() if "Engagement Rate" in df else None}


def hashtag_summary(df):
    rows = []
    for _, row in df.iterrows():
        for tag in row.get("_Hashtags", []):
            rows.append({"Hashtag": tag, "Engagement Rate": row.get("Engagement Rate"), "Reach": row.get("Reach")})
    if not rows:
        return pd.DataFrame(columns=["Hashtag", "Posts", "Average Engagement Rate", "Average Reach"])
    return pd.DataFrame(rows).groupby("Hashtag").agg(Posts=("Hashtag", "size"), **{"Average Engagement Rate": ("Engagement Rate", "mean"), "Average Reach": ("Reach", "mean")}).reset_index()


def top_posts(df, metric, limit=10, min_reach=0):
    if metric not in df:
        return df.iloc[0:0]
    d = df[df["Reach"].fillna(0) >= min_reach]
    return d.nlargest(limit, metric)

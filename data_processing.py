"""Workbook loading, validation, and reusable cleaning helpers."""
from pathlib import Path
import re
import pandas as pd

DEFAULT_DATA_FILE = Path(__file__).with_name("sugar_cosmetics_instagram_data.xlsx")
METRICS = ["Impressions", "Reach", "Likes", "Comments", "Shares", "Saves", "Profile Visits", "Follows"]
REQUIRED = ["Post Date", "Post Type", "Likes", "Comments", "Reach"]


def load_data(path=DEFAULT_DATA_FILE):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}. Place sugar_cosmetics_instagram_data.xlsx next to app.py.")
    book = pd.ExcelFile(path)
    if not book.sheet_names:
        raise ValueError("The Excel workbook has no sheets.")
    raw = pd.read_excel(book, sheet_name=book.sheet_names[0])
    raw.columns = [str(c).strip() for c in raw.columns]
    missing = [c for c in REQUIRED if c not in raw.columns]
    if missing:
        raise ValueError(f"Required columns are missing: {', '.join(missing)}. Found: {', '.join(raw.columns)}")
    return clean_data(raw), {"sheet": book.sheet_names[0], "rows_before": len(raw), "duplicate_rows": int(raw.duplicated().sum()), "columns": list(raw.columns)}


def clean_data(raw):
    """Coerce invalid dates/metrics to missing; retain all source rows for transparency."""
    df = raw.copy()
    df["Post Date"] = pd.to_datetime(df["Post Date"], errors="coerce")
    for col in METRICS:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] < 0, col] = pd.NA
    df["_row_id"] = [f"Row {i + 1}" for i in range(len(df))]
    df["Engagement Rate"] = pd.NA
    if all(c in df for c in ["Likes", "Comments", "Shares", "Saves", "Reach"]):
        denom = df["Reach"].where(df["Reach"] > 0)
        total = df[["Likes", "Comments", "Shares", "Saves"]].sum(axis=1, min_count=4)
        df["Engagement Rate"] = total.div(denom).mul(100)
    df["_Month"] = df["Post Date"].dt.to_period("M").dt.to_timestamp()
    df["_Weekday"] = df["Post Date"].dt.day_name()
    if "Hashtags" in df:
        df["_Hashtags"] = df["Hashtags"].fillna("").astype(str).apply(lambda s: list(dict.fromkeys(re.findall(r"#[\w]+", s.lower()))))
    else:
        df["_Hashtags"] = [[] for _ in range(len(df))]
    return df


def quality_report(df, info):
    rate_invalid = int(df["Engagement Rate"].isna().sum()) if "Engagement Rate" in df else None
    return {
        "rows": len(df), "valid_dates": int(df["Post Date"].notna().sum()),
        "missing_cells": int(df.drop(columns=["_row_id", "_Month", "_Weekday", "_Hashtags", "Engagement Rate"], errors="ignore").isna().sum().sum()),
        "duplicates": info.get("duplicate_rows", 0),
        "invalid_dates": int(df["Post Date"].isna().sum()),
        "zero_reach": int((df["Reach"] == 0).sum()) if "Reach" in df else None,
        "invalid_engagement_rates": rate_invalid,
    }

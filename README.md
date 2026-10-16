# SUGAR COSMETICS | Instagram Performance Analytics

An interactive Streamlit dashboard for exploring post-level Instagram performance from the supplied Excel workbook.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Keep `sugar_cosmetics_instagram_data.xlsx` beside `app.py`. The workbook is treated as source data and is never modified.

## Features

- Date, post type, campaign, and hashtag filters shared across all views.
- Overview KPIs and monthly volume/engagement trends.
- Top post rankings, post type comparisons, weekday analysis, hashtag summaries, and campaign/audience views.
- Engagement progression using available totals, with metric interpretation caveats.
- Searchable post-level explorer, filtered CSV export, and data-quality summary.
- Cached workbook loading with safe handling of invalid dates and negative metrics.

## Metric definitions and assumptions

- One source row represents one post. Total Posts counts filtered rows.
- Average Engagement Rate is the arithmetic mean of each eligible post's `(Likes + Comments + Shares + Saves) / Reach * 100`; missing engagement components and nonpositive reach do not produce a valid rate.
- Total Reach is the sum of post-level reach and may include the same account in multiple posts.
- Invalid dates and negative numeric metrics are set to missing for analysis, while source rows remain present. Exact duplicate rows are reported but not removed.
- No original post ID or caption exists in the supplied workbook. Generated row labels are display identifiers only.
- Hashtag statistics assign a post to each hashtag it contains; comparisons are descriptive and not causal.

## Dataset inspected

The supplied workbook currently has one sheet, 50,000 rows, and 14 columns. It covers 19 April 2024 through 19 April 2025. Its fields are Post Date, Post Type, Campaign Type, Hashtags, Audience Emotion, Engagement Source, Impressions, Reach, Likes, Comments, Shares, Saves, Profile Visits, and Follows. The initial inspection found no missing cells, exact duplicate rows, negative metrics, or rows where Reach exceeds Impressions. The app repeats the quality checks at runtime.

## Deployment

Deploy `app.py`, the helper modules, `requirements.txt`, and the workbook to a Streamlit hosting environment. Configure the workbook path or keep the file beside the app entry point. Do not publish confidential workbooks to a public deployment.

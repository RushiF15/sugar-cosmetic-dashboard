from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from data_processing import DEFAULT_DATA_FILE, load_data, quality_report, METRICS
from analytics import filter_data, kpis, hashtag_summary, top_posts
from visualizations import style, line, bar, funnel, PALETTE

st.set_page_config(page_title="Sugar Cosmetics | Instagram Analytics", page_icon="S", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
.stApp{background:linear-gradient(135deg,#fffafa 0%,#fff 55%,#fff5f8 100%);color:#392832}
h1,h2,h3{color:#421e2c!important} h1{font-family:'Playfair Display',serif!important;letter-spacing:-.4px}
.block-container{padding-top:2rem;max-width:1440px}
[data-testid="stMetric"]{background:linear-gradient(145deg,#fff,#fff7fa);border:1px solid #f0dce4;border-radius:16px;padding:18px 20px;box-shadow:0 5px 16px #6f26300b}
[data-testid="stMetricLabel"]{color:#765764!important;font-weight:600}
[data-testid="stMetricValue"]{color:#421e2c!important}
[data-testid="stMetricDelta"]{color:#765764!important}
[data-testid="stTabs"] [role="tab"]{color:#654653!important;font-weight:600}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#8f244b!important;border-bottom-color:#b83262!important}
[data-testid="stTabs"] [role="tab"]:hover{color:#8f244b!important}
[data-testid="stSidebar"]{background:#fff7fa;border-right:1px solid #f1dfe6}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label p{color:#492d39!important;font-weight:600}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stCaption p{color:#644451!important;opacity:1!important}
[data-testid="stSidebar"] input{color:#392832!important}
[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#fff!important;border:1px solid #d8b9c6!important;border-radius:9px!important;min-height:42px;box-shadow:none!important}
[data-testid="stSidebar"] [data-baseweb="select"]>div:hover{border-color:#a94468!important}
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"]{background:#8f2b50!important;border-radius:6px!important}
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"] *{color:#fff!important;fill:#fff!important}
[data-testid="stSidebar"] [data-baseweb="select"] [aria-label="Remove"]{color:#fff!important;fill:#fff!important;opacity:1!important}
[data-testid="stSidebar"] [data-baseweb="select"] svg{color:#704657!important;fill:#704657!important;opacity:1!important}
[data-testid="stSidebar"] [data-baseweb="select"] input{color:#392832!important}
[data-testid="stSidebar"] button{background:#9f3158!important;color:#fff!important;border:1px solid #9f3158!important;transition:background .15s ease,border-color .15s ease}
[data-testid="stSidebar"] button:hover{background:#76213f!important;color:#fff!important;border-color:#76213f!important}
[data-testid="stSidebar"] button:focus{color:#fff!important;box-shadow:0 0 0 2px #e5aec1!important}
.subtle{color:#765764;font-size:1.02rem;margin-top:-12px}
div[data-testid="stPlotlyChart"]{border:1px solid #f1e1e7;border-radius:16px;background:white;padding:8px}
[data-testid="stPlotlyChart"] iframe{background:#fff!important}
[data-testid="stMetric"]{min-height:116px;display:flex;flex-direction:column;justify-content:center}
[data-testid="stMetricValue"]{font-size:1.75rem;font-weight:700;line-height:1.2}
</style>""", unsafe_allow_html=True)

def compact(value):
    if pd.isna(value): return "—"
    n=float(value)
    if abs(n)>=1_000_000: return f"{n/1_000_000:.2f}M"
    if abs(n)>=100_000: return f"{n/1_000:.0f}K"
    if abs(n)>=10_000: return f"{n/1_000:.1f}K"
    return f"{n:,.0f}"

def available(df, col): return col in df and df[col].notna().any()

@st.cache_data(show_spinner="Reading and validating workbook…")
def get_data(path): return load_data(path)

st.sidebar.markdown("## SUGAR COSMETICS")
st.sidebar.caption("Instagram performance analytics")
try:
    df, info = get_data(str(DEFAULT_DATA_FILE))
except Exception as exc:
    st.error(f"Unable to load the dataset: {exc}")
    st.stop()

st.sidebar.markdown("### Filters")
dates=df["Post Date"].dropna()
date_value=None
if not dates.empty:
    bounds=(dates.min().date(),dates.max().date())
    date_value=st.sidebar.date_input("Post date range",value=bounds,min_value=bounds[0],max_value=bounds[1],key="filter_date")
post_opts=sorted(df["Post Type"].dropna().unique()) if available(df,"Post Type") else []
post_sel=st.sidebar.multiselect("Post type",post_opts,default=[],key="filter_post_type",help="Leave empty to include every post type.")
camp_opts=sorted(df["Campaign Type"].dropna().unique()) if available(df,"Campaign Type") else []
camp_sel=st.sidebar.multiselect("Campaign type",camp_opts,default=[],key="filter_campaign",help="Leave empty to include every campaign.") if camp_opts else None
tag_values=sorted({tag for tags in df["_Hashtags"] for tag in tags})
tag_sel=st.sidebar.multiselect("Hashtag",tag_values,default=[],format_func=lambda t:"#"+t.lstrip("#"),key="filter_hashtag",help="Leave empty to include posts with any hashtag.") if tag_values else None
if st.sidebar.button("Reset filters",width="stretch"):
    st.session_state.clear(); st.rerun()
st.sidebar.divider()
st.sidebar.markdown("### Dataset")
st.sidebar.caption(f"{info['sheet']} · {len(df):,} rows · {len(info['columns'])} columns")
if dates.size: st.sidebar.caption(f"{dates.min():%d %b %Y} — {dates.max():%d %b %Y}")

filtered=filter_data(df,date_value,post_sel,camp_sel,tag_sel)
st.title("SUGAR COSMETICS | Instagram Performance Analytics")
st.markdown('<p class="subtle">Turning social media data into actionable marketing insights.</p>',unsafe_allow_html=True)
selected_dates = f"{date_value[0]:%d %b %Y} – {date_value[1]:%d %b %Y}" if isinstance(date_value,(tuple,list)) and len(date_value)==2 else "All available dates"
st.caption(f"Showing **{len(filtered):,} of {len(df):,} source records** · Date range: **{selected_dates}**. Empty category filters include all values.")
if len(filtered) != len(df):
    st.caption(f"{len(df)-len(filtered):,} source rows are outside the current filters; the workbook still contains {len(df):,} records in total.")
q_full=quality_report(df,info)
if q_full["invalid_dates"]:
    st.warning(f"{q_full['invalid_dates']:,} source rows have invalid dates and cannot be included in a date-range selection. They remain available in the data-quality report.")
if len(filtered)==0:
    st.warning("No posts match these filters. Adjust or reset filters to continue.")
    st.stop()

tabs=st.tabs(["Overview","Content Performance","Timing & Trends","Hashtags","Audience & Campaigns","Data Explorer"])
with tabs[0]:
    st.subheader("Performance overview")
    k=kpis(filtered); cols=st.columns(5)
    labels=[("Total Posts",k["posts"],"Valid post rows"),("Total Likes",k["likes"],"Sum of post likes"),("Total Comments",k["comments"],"Sum of post comments"),("Total Reach",k["reach"],"Sum of post-level reach; not unique period reach"),("Avg. Engagement Rate",k["avg_er"],"Mean per-post rate; positive reach only")]
    for c,(label,value,help_text) in zip(cols,labels):
        display=f"{value:.2f}%" if label.startswith("Avg") and pd.notna(value) else compact(value)
        exact=f"{value:,.2f}%" if label.startswith("Avg") and pd.notna(value) else (f"{value:,.0f}" if pd.notna(value) else "Unavailable")
        c.metric(label,display,help=f"{help_text}. Exact value: {exact}")
    a,b=st.columns(2)
    monthly=filtered.dropna(subset=["_Month"]).groupby("_Month").agg(Posts=("_row_id","size"),**{"Avg. Engagement Rate":("Engagement Rate","mean")}).reset_index().sort_values("_Month")
    with a: st.plotly_chart(line(monthly,"_Month","Posts","Posts published per month"),width="stretch")
    with b:
        if monthly["Avg. Engagement Rate"].notna().any(): st.plotly_chart(line(monthly,"_Month","Avg. Engagement Rate","Average engagement rate by month"),width="stretch")
        else: st.info("Engagement trend unavailable: no posts with valid positive reach and engagement metrics.")
    a,b=st.columns(2)
    with a:
        types=filtered["Post Type"].value_counts().rename_axis("Post Type").reset_index(name="Posts")
        st.plotly_chart(style(px.pie(types,names="Post Type",values="Posts",hole=.55,title="Post type mix",color_discrete_sequence=PALETTE)),width="stretch")
    with b:
        if all(c in filtered for c in ["Impressions","Reach","Likes","Comments","Shares","Saves"]):
            funnel_data=pd.DataFrame({"Metric":["Impressions","Reach","Likes","Comments","Shares","Saves"],"Total":[filtered[c].sum() for c in ["Impressions","Reach","Likes","Comments","Shares","Saves"]]})
            st.plotly_chart(funnel(funnel_data),width="stretch")
            st.caption("These metrics have different meanings and are not strictly sequential conversion stages. Differences do not represent exact user drop-off.")
        else: st.info("Engagement progression needs impressions, reach, likes, comments, shares, and saves.")
    st.markdown("#### Observations")
    highest=filtered.groupby("Post Type")["Engagement Rate"].mean().dropna().sort_values(ascending=False)
    if len(highest): st.write(f"**{highest.index[0]}** posts have the highest average engagement rate in this selection ({highest.iloc[0]:.2f}%). This is descriptive and does not establish causation.")
    else: st.write("There are not enough valid reach records to compare post type engagement rates.")

with tabs[1]:
    st.subheader("Content performance")
    threshold=st.slider("Minimum reach for engagement rate ranking",0, max(1000,int(filtered["Reach"].max())),0,step=max(1,int(filtered["Reach"].max()/1000)))
    panes=st.columns(3)
    for col,metric,title,fmt in zip(panes,["Likes","Comments","Engagement Rate"],["Top posts by likes","Top posts by comments","Top posts by engagement rate"],[",.0f",",.0f",".2f"]):
        with col:
            t=top_posts(filtered,metric,10,threshold if metric=="Engagement Rate" else 0).copy()
            if len(t):
                t["Post"] = t.get("Post ID",t.get("Caption",t["_row_id"]))
                fig=px.bar(t.sort_values(metric),x=metric,y="Post",orientation="h",title=title,hover_data=["Post Date","Post Type","Reach"],color_discrete_sequence=[PALETTE[0]])
                st.plotly_chart(style(fig,400),width="stretch")
            else: st.info("No eligible records for this ranking.")
    st.caption("No original post ID or caption was provided, so row labels use transparent row-level IDs.")
    if all(c in filtered for c in ["Likes","Comments","Shares","Saves"]):
        comp=filtered.groupby("Post Type")[["Likes","Comments","Shares","Saves"]].mean().reset_index().melt("Post Type",var_name="Metric",value_name="Average per post")
        st.plotly_chart(style(px.bar(comp,x="Post Type",y="Average per post",color="Metric",barmode="group",title="Average interactions by post type",color_discrete_sequence=PALETTE)),width="stretch")
        best=filtered.groupby("Post Type")["Engagement Rate"].mean().dropna().sort_values(ascending=False)
        if len(best): st.info(f"Best-performing post type by average engagement rate: **{best.index[0]}** ({best.iloc[0]:.2f}%).")
    st.markdown("#### Post-level detail")
    show=[c for c in df.columns if not c.startswith("_")]+["_row_id"]
    st.dataframe(filtered[show].sort_values("Post Date",ascending=False),width="stretch",height=380)

with tabs[2]:
    st.subheader("Timing & trends")
    a,b=st.columns(2)
    with a: st.plotly_chart(line(monthly,"_Month","Posts","Posts published by month"),width="stretch")
    with b:
        weekday_order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        wd=filtered.groupby("_Weekday")["Engagement Rate"].mean().reindex(weekday_order).dropna().rename("Average Engagement Rate").reset_index()
        if len(wd): st.plotly_chart(style(px.bar(wd,x="_Weekday",y="Average Engagement Rate",title="Average engagement by weekday",color_discrete_sequence=[PALETTE[0]])),width="stretch")
        else: st.info("Weekday engagement unavailable for the selected records.")
    if len(monthly):
        peak=monthly.sort_values("Posts",ascending=False).iloc[0]
        st.write(f"Posting volume was highest in **{peak['_Month']:%B %Y}** with **{int(peak.Posts):,} posts**.")
    st.caption("The dataset has dates but no publication time, so time-of-day performance cannot be assessed.")

with tabs[3]:
    st.subheader("Hashtag analysis")
    hs=hashtag_summary(filtered)
    if hs.empty: st.info("Hashtag analysis is unavailable because this selection has no usable hashtag values.")
    else:
        min_posts=st.slider("Minimum associated posts",1,100,10)
        hs=hs[hs["Posts"]>=min_posts].sort_values("Posts",ascending=False)
        a,b=st.columns(2)
        with a: st.plotly_chart(style(px.bar(hs.head(15),x="Hashtag",y="Posts",title="Most frequent hashtags",color_discrete_sequence=[PALETTE[0]])),width="stretch")
        with b:
            eligible=hs[hs["Average Engagement Rate"].notna()].sort_values("Average Engagement Rate",ascending=False).head(15)
            if len(eligible): st.plotly_chart(style(px.bar(eligible,x="Hashtag",y="Average Engagement Rate",title="Average engagement by hashtag",color_discrete_sequence=[PALETTE[1]])),width="stretch")
            else: st.info("No hashtag records have a valid engagement rate.")
        st.dataframe(hs,width="stretch")
        st.caption("Posts can contain multiple hashtags, so each post contributes to every tag it contains. These are descriptive associations and do not demonstrate causation.")

with tabs[4]:
    st.subheader("Audience & campaign insights")
    available_fields=[c for c in ["Audience Emotion","Engagement Source","Campaign Type","Profile Visits","Follows"] if available(filtered,c)]
    if not available_fields: st.info("No usable audience or campaign fields are available in this dataset.")
    a,b=st.columns(2)
    for col,name in zip([a,b],["Audience Emotion","Engagement Source"]):
        with col:
            if name in available_fields:
                v=filtered[name].value_counts().rename_axis(name).reset_index(name="Posts")
                st.plotly_chart(style(px.bar(v,x=name,y="Posts",title=f"{name} distribution",color_discrete_sequence=PALETTE)),width="stretch")
    if "Campaign Type" in available_fields:
        camp=filtered.groupby("Campaign Type").agg(Posts=("_row_id","size"),**{"Average Engagement Rate":("Engagement Rate","mean"),"Average Reach":("Reach","mean")}).reset_index()
        st.plotly_chart(style(px.bar(camp,x="Campaign Type",y="Average Engagement Rate",title="Average engagement by campaign type",hover_data=["Posts","Average Reach"],color_discrete_sequence=[PALETTE[0]])),width="stretch")
        st.dataframe(camp,width="stretch")
    metrics=[c for c in ["Profile Visits","Follows"] if c in available_fields]
    if metrics:
        stats=pd.DataFrame({"Metric":metrics,"Total":[filtered[c].sum() for c in metrics]})
        st.plotly_chart(style(px.bar(stats,x="Metric",y="Total",title="Profile visits and follows · totals",color_discrete_sequence=PALETTE)),width="stretch")
        st.caption("Follows are reported as recorded counts; they are not a follower-growth rate.")
    st.caption("No age, gender, or location fields were supplied, so demographic conclusions are not available.")

with tabs[5]:
    st.subheader("Data explorer")
    st.write(f"Selected date range: **{selected_dates}** · **{len(filtered):,} filtered records**")
    search=st.text_input("Search visible fields",placeholder="Search post type, campaign, hashtag, emotion…")
    table=filtered.copy()
    if search:
        mask=table.astype(str).apply(lambda col: col.str.contains(search,case=False,na=False)).any(axis=1)
        table=table[mask]
    st.caption(f"{len(table):,} records match the table search.")
    st.dataframe(table[[c for c in table.columns if not c.startswith("_")]+["_row_id"]],width="stretch",height=430)
    csv=table[[c for c in table.columns if not c.startswith("_")]+["_row_id"]].to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download filtered records as CSV",csv,"sugar_cosmetics_filtered_posts.csv","text/csv")
    st.markdown("#### Data quality")
    q=quality_report(df,info)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Source rows",f"{info['rows_before']:,}")
    c2.metric("Valid dates",f"{q['valid_dates']:,}")
    c3.metric("Exact duplicate rows",f"{q['duplicates']:,}")
    c4.metric("Rows with zero reach",f"{q['zero_reach']:,}" if q['zero_reach'] is not None else "N/A")
    invalid_er = q.get("invalid_engagement_rates", int(df["Engagement Rate"].isna().sum()))
    st.caption(f"Missing source cells after numeric/date validation: {q['missing_cells']:,}. Invalid dates: {q['invalid_dates']:,}. Rows with invalid engagement rates (missing component or nonpositive reach): {invalid_er:,}. Source rows are retained; invalid values become missing and are excluded only where a calculation requires them. This source contains no original post identifier or caption.")

period=f"{dates.min():%d %b %Y} – {dates.max():%d %b %Y}" if not dates.empty else "Date range unavailable"
st.markdown(f"<hr><div style='text-align:center;color:#846a76;font-size:.82rem'>SUGAR COSMETICS · Instagram Performance Analytics · {period}<br>Findings reflect the supplied dataset.</div>",unsafe_allow_html=True)

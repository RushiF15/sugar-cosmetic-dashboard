"""Reusable Plotly chart constructors with a consistent palette."""
import plotly.express as px
import plotly.graph_objects as go

ROSE = "#b83262"
PALETTE = ["#b83262", "#df7899", "#7b2345", "#e9a8bb", "#563341", "#c75a7d"]


def style(fig, height=360):
    fig.update_layout(height=height, template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#fffdfd",
                      margin=dict(l=18, r=18, t=54, b=42),
                      font=dict(family="DM Sans, Arial, sans-serif", size=12, color="#392832"),
                      title=dict(font=dict(size=17, color="#421e2c"), x=0.02, xanchor="left"),
                      colorway=PALETTE, legend_title_text="",
                      legend=dict(font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      hoverlabel=dict(bgcolor="white", font_color="#392832", font_size=12))
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#eadde2", tickfont=dict(size=11, color="#644451"))
    fig.update_yaxes(showgrid=True, gridcolor="#f2e8ec", zeroline=False, linecolor="#eadde2", tickfont=dict(size=11, color="#644451"))
    # Plotly Express otherwise exposes implementation column names such as _Month.
    friendly = {"_Month": "Month", "_Weekday": "Weekday", "Engagement Rate": "Engagement rate (%)",
                "Average Engagement Rate": "Average engagement rate (%)", "Average per post": "Average interactions per post"}
    if fig.layout.xaxis.title.text:
        fig.update_xaxes(title_text=friendly.get(fig.layout.xaxis.title.text, fig.layout.xaxis.title.text.replace("_", " ")))
    if fig.layout.yaxis.title.text:
        fig.update_yaxes(title_text=friendly.get(fig.layout.yaxis.title.text, fig.layout.yaxis.title.text.replace("_", " ")))
    for axis_name in ("xaxis", "yaxis"):
        axis = getattr(fig.layout, axis_name)
        axis_title = (axis.title.text or "").lower()
        update_axis = fig.update_xaxes if axis_name == "xaxis" else fig.update_yaxes
        if "engagement rate" in axis_title:
            update_axis(tickformat=".2f", ticksuffix="%")
        elif axis_title and axis.type != "date":
            update_axis(tickformat="~s")
    return fig


def bar(data, x, y, title, color=None, horizontal=False):
    fig = px.bar(data, x=y if horizontal else x, y=x if horizontal else y, color=color, title=title,
                 orientation="h" if horizontal else "v", color_discrete_sequence=PALETTE)
    return style(fig)


def line(data, x, y, title, color=None):
    fig = px.line(data, x=x, y=y, color=color, markers=True, title=title,
                  color_discrete_sequence=PALETTE, labels={x: "Month" if x == "_Month" else x.replace("_", " "),
                  y: y.replace("_", " ")})
    style(fig)
    if x == "_Month":
        fig.update_xaxes(tickformat="%b %Y", title_text="Month", tickangle=-25)
    if "Engagement Rate" in y:
        fig.update_yaxes(tickformat=".2f", ticksuffix="%", title_text="Average engagement rate (%)")
        for trace in fig.data:
            trace.hovertemplate = "%{x|%b %Y}<br>Average engagement rate: %{y:.2f}%<extra></extra>"
    elif y.lower() in {"posts", "total", "reach", "likes", "comments", "shares", "saves", "impressions"}:
        fig.update_yaxes(tickformat="~s")
    return fig


def funnel(data):
    fig = go.Figure(go.Funnel(y=data["Metric"], x=data["Total"], textinfo="value+percent initial", marker={"color": PALETTE}))
    fig.update_layout(title="Engagement progression · totals", xaxis_title="Post-level total")
    return style(fig)

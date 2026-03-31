import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# カテゴリごとの色設定
CATEGORY_COLORS = {
    "教育": "#4CAF50",
    "IT": "#2196F3",
    "コーチング": "#FF9800",
    "経営": "#9C27B0",
}


def build_heatmap(mapping_data: dict) -> go.Figure:
    """スキル×職種のヒートマップを生成する"""
    skills = mapping_data["skills"]
    job_types = mapping_data["job_types"]

    job_names = [j["name"] for j in job_types]
    # 2次元配列: rows=職種, cols=スキル
    z = [[j["scores"].get(s, 0) for s in skills] for j in job_types]

    # overall_matchでソート（降順）
    sorted_pairs = sorted(zip(z, job_names), key=lambda x: sum(x[0]) / len(x[0]), reverse=True)
    z_sorted = [pair[0] for pair in sorted_pairs]
    job_names_sorted = [pair[1] for pair in sorted_pairs]

    fig = go.Figure(data=go.Heatmap(
        z=z_sorted,
        x=skills,
        y=job_names_sorted,
        colorscale="RdYlGn",
        zmin=0,
        zmax=100,
        text=[[str(v) for v in row] for row in z_sorted],
        texttemplate="%{text}",
        textfont={"size": 12},
        hovertemplate="職種: %{y}<br>スキル: %{x}<br>スコア: %{z}<extra></extra>",
    ))

    fig.update_layout(
        title="スキル × 職種 マッチ度マトリクス",
        xaxis_title="スキル",
        yaxis_title="職種",
        height=420,
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family="sans-serif"),
    )
    return fig


def build_radar(job_data: dict, skills: list[str]) -> go.Figure:
    """選択した職種のレーダーチャートを生成する"""
    scores = [job_data["scores"].get(s, 0) for s in skills]
    # レーダーチャートは閉じる必要があるため先頭要素を末尾にも追加
    scores_closed = scores + [scores[0]]
    skills_closed = skills + [skills[0]]

    color = CATEGORY_COLORS.get(job_data.get("category", ""), "#607D8B")

    fig = go.Figure(data=go.Scatterpolar(
        r=scores_closed,
        theta=skills_closed,
        fill="toself",
        fillcolor=color,
        opacity=0.3,
        line=dict(color=color, width=2),
        name=job_data["name"],
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11)),
        ),
        title=f"{job_data['name']}　マッチ度: {job_data['overall_match']}",
        height=380,
        margin=dict(l=30, r=30, t=60, b=30),
        showlegend=False,
        font=dict(family="sans-serif"),
    )
    return fig


def build_overall_bar(mapping_data: dict) -> go.Figure:
    """職種ごとの総合マッチ度の棒グラフを生成する"""
    job_types = mapping_data["job_types"]
    names = [j["name"] for j in job_types]
    scores = [j["overall_match"] for j in job_types]
    categories = [j.get("category", "") for j in job_types]
    colors = [CATEGORY_COLORS.get(c, "#607D8B") for c in categories]

    # スコア降順でソート
    sorted_data = sorted(zip(scores, names, colors), reverse=True)
    scores_s, names_s, colors_s = zip(*sorted_data)

    fig = go.Figure(data=go.Bar(
        x=list(scores_s),
        y=list(names_s),
        orientation="h",
        marker_color=list(colors_s),
        text=[f"{s}" for s in scores_s],
        textposition="outside",
        hovertemplate="%{y}: %{x}点<extra></extra>",
    ))

    fig.update_layout(
        title="職種別 総合マッチ度ランキング",
        xaxis=dict(title="マッチ度スコア", range=[0, 110]),
        yaxis=dict(autorange="reversed"),
        height=380,
        margin=dict(l=10, r=40, t=50, b=10),
        font=dict(family="sans-serif"),
    )
    return fig

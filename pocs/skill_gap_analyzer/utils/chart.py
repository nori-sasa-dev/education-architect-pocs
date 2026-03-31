import plotly.graph_objects as go

# 優先度ごとの色
PRIORITY_COLORS = {
    "高": "#F44336",
    "中": "#FF9800",
    "低": "#4CAF50",
}


def build_gap_bar(gap_data: dict) -> go.Figure:
    """現在レベル vs 必要レベルの横棒グラフ（ギャップを視覚化）"""
    skills = [s["skill"] for s in gap_data["required_skills"]]
    current = [s["current_level"] for s in gap_data["required_skills"]]
    required = [s["required_level"] for s in gap_data["required_skills"]]
    priorities = [s["priority"] for s in gap_data["required_skills"]]

    # ギャップが大きい順にソート
    sorted_data = sorted(
        zip(skills, current, required, priorities),
        key=lambda x: x[2] - x[1],
        reverse=True,
    )
    skills_s, current_s, required_s, priorities_s = zip(*sorted_data)

    fig = go.Figure()

    # 現在レベル（塗りつぶし）
    fig.add_trace(go.Bar(
        name="現在のレベル",
        x=list(current_s),
        y=list(skills_s),
        orientation="h",
        marker_color="#42A5F5",
        hovertemplate="%{y}<br>現在: %{x}<extra></extra>",
    ))

    # 必要レベル（枠線のみ）
    fig.add_trace(go.Bar(
        name="必要レベル",
        x=[r - c for r, c in zip(required_s, current_s)],
        y=list(skills_s),
        orientation="h",
        marker_color=[PRIORITY_COLORS.get(p, "#E0E0E0") for p in priorities_s],
        marker_line_color="rgba(0,0,0,0)",
        opacity=0.6,
        base=list(current_s),
        hovertemplate="%{y}<br>ギャップ: %{x}<extra></extra>",
    ))

    fig.update_layout(
        title="スキルギャップ分析（青=現在、色付き=不足分）",
        barmode="stack",
        xaxis=dict(title="レベル", range=[0, 110]),
        yaxis=dict(autorange="reversed"),
        height=max(300, len(skills) * 45 + 80),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="sans-serif"),
    )
    return fig


def build_radar_comparison(gap_data: dict) -> go.Figure:
    """現在レベル vs 必要レベルのレーダーチャート"""
    skills = [s["skill"] for s in gap_data["required_skills"]]
    current = [s["current_level"] for s in gap_data["required_skills"]]
    required = [s["required_level"] for s in gap_data["required_skills"]]

    # レーダーチャートを閉じる
    skills_c = skills + [skills[0]]
    current_c = current + [current[0]]
    required_c = required + [required[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=required_c,
        theta=skills_c,
        fill="toself",
        fillcolor="rgba(244,67,54,0.1)",
        line=dict(color="#F44336", width=2, dash="dash"),
        name="必要レベル",
    ))
    fig.add_trace(go.Scatterpolar(
        r=current_c,
        theta=skills_c,
        fill="toself",
        fillcolor="rgba(66,165,245,0.3)",
        line=dict(color="#42A5F5", width=2),
        name="現在のレベル",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=10)),
        ),
        title=f"現在 vs 必要レベル比較",
        height=380,
        margin=dict(l=30, r=30, t=60, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        font=dict(family="sans-serif"),
    )
    return fig


def build_priority_pie(gap_data: dict) -> go.Figure:
    """優先度別スキル数の円グラフ"""
    from collections import Counter
    counts = Counter(s["priority"] for s in gap_data["required_skills"])
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [PRIORITY_COLORS.get(l, "#9E9E9E") for l in labels]

    fig = go.Figure(data=go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.4,
        textinfo="label+value",
        hovertemplate="%{label}: %{value}件<extra></extra>",
    ))
    fig.update_layout(
        title="優先度別スキルギャップ数",
        height=300,
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family="sans-serif"),
        showlegend=False,
    )
    return fig

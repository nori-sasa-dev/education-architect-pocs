"""持ち味の軌跡（点→線）を可視化するユーティリティ。"""

import altair as alt
import pandas as pd

# 濃淡の表示記号（Markdownダウンロード等のテキスト表現用）
STRENGTH_MARK = {"濃": "●", "中": "◐", "薄": "○"}

# 濃淡を発揮度の数値に変換（棒グラフの高さ）
STRENGTH_VALUE = {"濃": 3, "中": 2, "薄": 1}

# 持ち味タイプごとのラベルと説明（表示名は「いつ出るか」が伝わる直感的な表現）
TYPE_LABEL = {
    "核": ("🪨 ぶれない強み", "いつも安定して出る、あなたの土台"),
    "芽": ("🌱 伸びる強み", "期を追って強まってきた、成長中の強み"),
    "状況依存": ("✨ ここぞの強み", "特定の場面で際立つ、あなたが輝く条件"),
}

# タイプごとの色（棒グラフ）。安定=青 / 成長=緑 / ここぞ=橙
TYPE_COLOR = {
    "核": "#2E86C1",
    "芽": "#27AE60",
    "状況依存": "#E67E22",
}


def trajectory_table(trajectory: list[dict]) -> str:
    """軌跡を Markdown テーブル文字列に変換する。"""
    header = "| 期 | 濃淡 | 証拠となった出来事 |\n|---|:---:|---|"
    rows = []
    for t in trajectory:
        mark = STRENGTH_MARK.get(t.get("strength", ""), "・")
        rows.append(f"| {t['period']} | {mark} | {t['evidence']} |")
    return header + "\n" + "\n".join(rows)


def trajectory_sparkline(trajectory: list[dict]) -> str:
    """軌跡の濃淡を1行のスパークラインにする（例：○ → ○ → ◐ → ●）。"""
    marks = [STRENGTH_MARK.get(t.get("strength", ""), "・") for t in trajectory]
    return " → ".join(marks)


def trajectory_chart(trajectory: list[dict], trait_type: str = "核") -> alt.Chart:
    """軌跡を「いつ・どれくらい発揮したか」の棒グラフにする。

    横軸=期（左が古い→右が新しい）、縦軸=発揮度（薄・中・濃）。
    棒の色は持ち味タイプ（ぶれない/伸びる/ここぞ）で変える。
    """
    df = pd.DataFrame(
        [
            {
                "期": t["period"],
                "発揮度": STRENGTH_VALUE.get(t.get("strength", ""), 0),
                "出来事": t.get("evidence", ""),
            }
            for t in trajectory
        ]
    )
    periods = df["期"].tolist()  # JSONの順序（時系列）をそのまま使う
    color = TYPE_COLOR.get(trait_type, "#2E86C1")
    return (
        alt.Chart(df)
        .mark_bar(size=44, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=color)
        .encode(
            x=alt.X("期:N", sort=periods, axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y(
                "発揮度:Q",
                scale=alt.Scale(domain=[0, 3]),
                axis=alt.Axis(
                    values=[1, 2, 3],
                    labelExpr="datum.value==1?'薄':datum.value==2?'中':datum.value==3?'濃':''",
                    title=None,
                ),
            ),
            tooltip=[alt.Tooltip("期:N"), alt.Tooltip("出来事:N", title="出来事")],
        )
        .properties(height=170)
    )

"""持ち味の軌跡（点→線）を濃淡で可視化するユーティリティ。"""

# 濃淡の表示記号。グラフを使わず、誰でも直感的に読めるシンプルな表現にする。
STRENGTH_MARK = {"濃": "●", "中": "◐", "薄": "○"}

# 持ち味タイプごとのラベルと色（バッジ表示用）
TYPE_LABEL = {
    "核": ("🪨 核", "環境を問わず安定して現れる、あなたの土台"),
    "芽": ("🌱 芽", "期を追って強まってきた、成長中の持ち味"),
    "状況依存": ("✨ 状況依存", "特定の場面で際立つ、あなたが輝く条件"),
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

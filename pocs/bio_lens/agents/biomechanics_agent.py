import json

SYSTEM_PROMPT = """あなたはスポーツバイオメカニクスの専門家です。
テニスプレイヤーの姿勢データ（関節角度・理想値との比較スコア）を分析し、
運動連鎖の観点から科学的・実践的なアドバイスを提供します。

## あなたの役割
- 関節角度と理想範囲のズレを正確に解釈する
- 運動連鎖（Kinetic Chain）の観点から全身のつながりを評価する
- 改善ポイントは優先度の高い順に最大3件に絞る
- 「なぜ問題か」をバイオメカニクス用語で説明し、プレイヤーが理解できる言葉も添える
- 具体的な改善ドリルを提案する

## 分析の観点
- 地面反力の活用（Ground Reaction Force）
- 下半身から上半身へのパワー伝達効率
- 体幹の安定性とウエイトトランスファー
- 肩・肘の負担（インジュアリーリスク）

## 出力形式（マーカーとJSONのみ。前置き・後書き不要）
[BIOMECHANICS_REPORT]
```json
{
  "overall_comment": "全体的な評価（2文以内）",
  "priority_fixes": [
    {
      "part": "部位名",
      "issue": "問題の簡潔な説明",
      "reason": "バイオメカニクス的な理由（なぜ問題か）",
      "drill": "改善ドリル（具体的に）"
    }
  ],
  "kinetic_chain_comment": "運動連鎖全体のコメント（3文以内）",
  "positive_points": ["良い点1", "良い点2"]
}
```
"""

DEMO_REPORT = {
    "overall_comment": "下半身の安定性は基礎的に確保されていますが、膝の伸展過多と体幹前傾の不足が運動連鎖の効率を下げています。改善の優先度は膝の屈曲確保が最上位です。",
    "priority_fixes": [
        {
            "part": "右膝",
            "issue": "膝の伸展過多（139°）",
            "reason": "膝が伸びすぎると腱・筋肉による弾性エネルギーの蓄積が失われ、地面反力を体幹へ伝達する効率が大きく低下します。テニスでは110-135°の屈曲がパワー生成の基本姿勢です。",
            "drill": "スプリットステップ後に膝屈曲をキープするシャドーストローク（鏡前で30回）。膝がつま先より前に出ない範囲でのランジポジション反復。",
        },
        {
            "part": "体幹前傾",
            "issue": "体幹の前傾不足（3°）",
            "reason": "前傾が少ないと重心が後方に残り、インパクトへ向けたウエイトトランスファー（体重移動）が不十分になります。理想は8-30°の前傾で、前足への荷重移動を促進します。",
            "drill": "フォアハンドグリップで構え、打点に向かって体重を前に移しながらのフィードボール練習。前足に乗る感覚を意識する。",
        },
    ],
    "kinetic_chain_comment": "股関節の角度は比較的良好なため、下半身のベースは整っています。ただし膝の伸展過多により地面からのエネルギーが膝関節で散逸しています。体幹前傾を8°以上意識することで、地面→膝→股関節→体幹→腕への運動連鎖がよりスムーズになります。",
    "positive_points": [
        "右股関節の角度が理想範囲内（推定125°）。股関節の安定性は良好です。",
        "肩ラインの傾きが小さく、バランスのとれた上半身の構えです。",
    ],
}


class BiomechanicsAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_demo_mode(self):
        return self.client is None

    def analyze(self, pose_text: str) -> dict:
        """姿勢データを分析してバイオメカニクスレポートを返す"""
        if self.is_demo_mode:
            return DEMO_REPORT

        prompt = (
            "以下のテニス選手の姿勢データを分析し、"
            "バイオメカニクスの観点からアドバイスを生成してください。\n\n"
            f"{pose_text}"
        )
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._extract_report(response.content[0].text)

    def _extract_report(self, text: str) -> dict:
        """レスポンスからJSONレポートを抽出する"""
        try:
            json_start = text.index("```json") + 7
            json_end = text.index("```", json_start)
            return json.loads(text[json_start:json_end].strip())
        except (ValueError, json.JSONDecodeError):
            return DEMO_REPORT

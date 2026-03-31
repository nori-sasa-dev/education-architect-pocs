import math
import cv2
import mediapipe as mp
import numpy as np
import urllib.request
import os

# モデルファイルは /tmp に保存（Streamlit Cloud でも書き込み可能）
MODEL_PATH = "/tmp/pose_landmarker_lite.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)

# テニスバイオメカニクスの理想範囲: {部位: (最小, 最大, 説明)}
IDEAL_RANGES = {
    "右肘":   (80,  150, "スイング中: 80-120°、フォロースルー: 120-150°"),
    "左肘":   (80,  150, ""),
    "右膝":   (110, 135, "パワー生成の理想屈曲範囲: 110-135°"),
    "左膝":   (110, 135, ""),
    "右股関節": (100, 155, "推進力生成の理想範囲: 100-155°"),
    "左股関節": (100, 155, ""),
    "右肩":   (60,  130, "スイング軌道に関わる肩の開き角度"),
    "体の傾き": (0,   8,  "肩ラインの水平度（0が理想）"),
    "体幹前傾": (8,   30,  "前傾8-30°が効率的な重心位置"),
}

# 角度テキストをオーバーレイする関節とそのランドマークインデックス
_OVERLAY_MAP = {
    "右肘":   14,  # RIGHT_ELBOW
    "左肘":   13,  # LEFT_ELBOW
    "右膝":   26,  # RIGHT_KNEE
    "左膝":   25,  # LEFT_KNEE
    "右股関節": 24,  # RIGHT_HIP
    "左股関節": 23,  # LEFT_HIP
}

# 描画用ポーズコネクション
_POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),  # 上半身
    (11, 23), (12, 24), (23, 24),                       # 胴体
    (23, 25), (25, 27), (24, 26), (26, 28),             # 下半身
    (27, 29), (29, 31), (28, 30), (30, 32),             # 足
]


def _ensure_model():
    """モデルファイルを /tmp にダウンロード（初回のみ）"""
    if not os.path.exists(MODEL_PATH):
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def _draw_landmarks(image: np.ndarray, landmarks) -> np.ndarray:
    """ランドマークとコネクションを OpenCV で描画する"""
    h, w = image.shape[:2]
    points = {}
    for idx, lm in enumerate(landmarks):
        x, y = int(lm.x * w), int(lm.y * h)
        points[idx] = (x, y)
        cv2.circle(image, (x, y), 4, (0, 255, 0), -1)
    for start, end in _POSE_CONNECTIONS:
        if start in points and end in points:
            cv2.line(image, points[start], points[end], (0, 128, 255), 2)
    return image


def analyze_pose(frame: np.ndarray) -> tuple[np.ndarray, dict | None, dict | None]:
    """
    フレームに姿勢推定とバイオメカニクス分析を適用する。
    戻り値: (角度オーバーレイ付きスケルトン画像, 関節角度データ, スコアデータ)
    姿勢が検出できない場合、角度とスコアはNone。
    """
    _ensure_model()

    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
    )

    skeleton_frame = frame.copy()

    with mp.tasks.vision.PoseLandmarker.create_from_options(options) as landmarker:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = landmarker.detect(mp_image)

        if not result.pose_landmarks:
            return skeleton_frame, None, None

        landmarks = result.pose_landmarks[0]
        _draw_landmarks(skeleton_frame, landmarks)
        angles = _calculate_angles(landmarks)
        scores = _calculate_scores(angles)
        annotated = _draw_angle_overlay(skeleton_frame, landmarks, angles, frame.shape)

    return annotated, angles, scores


def _angle_3pts(a, b, c) -> float:
    """3点から角度（度）を計算する。bが頂点。"""
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])
    ba = a - b
    bc = c - b
    cos_a = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return round(float(np.degrees(np.arccos(np.clip(cos_a, -1.0, 1.0)))), 1)


def _calculate_angles(lm) -> dict:
    """主要な関節角度とバイオメカニクス指標を計算する"""
    angles = {}

    # 肘（肩→肘→手首）
    angles["右肘"] = _angle_3pts(lm[12], lm[14], lm[16])  # RIGHT_SHOULDER→ELBOW→WRIST
    angles["左肘"] = _angle_3pts(lm[11], lm[13], lm[15])  # LEFT_SHOULDER→ELBOW→WRIST

    # 膝（腰→膝→足首）
    angles["右膝"] = _angle_3pts(lm[24], lm[26], lm[28])  # RIGHT_HIP→KNEE→ANKLE
    angles["左膝"] = _angle_3pts(lm[23], lm[25], lm[27])  # LEFT_HIP→KNEE→ANKLE

    # 股関節（肩→腰→膝）
    angles["右股関節"] = _angle_3pts(lm[12], lm[24], lm[26])  # RIGHT_SHOULDER→HIP→KNEE
    angles["左股関節"] = _angle_3pts(lm[11], lm[23], lm[25])  # LEFT_SHOULDER→HIP→KNEE

    # 肩（左肩→右肩→右肘）
    angles["右肩"] = _angle_3pts(lm[11], lm[12], lm[14])  # LEFT_SHOULDER→RIGHT_SHOULDER→ELBOW

    # 肩ラインの傾き（左右肩のy座標差）
    angles["体の傾き"] = round(abs(lm[11].y - lm[12].y) * 100, 1)

    # 体幹前傾（肩中点→腰中点のベクトルと垂直線の角度）
    s_mid_x = (lm[11].x + lm[12].x) / 2
    s_mid_y = (lm[11].y + lm[12].y) / 2
    h_mid_x = (lm[23].x + lm[24].x) / 2
    h_mid_y = (lm[23].y + lm[24].y) / 2
    dx = s_mid_x - h_mid_x
    dy = abs(s_mid_y - h_mid_y) + 1e-6
    angles["体幹前傾"] = round(math.degrees(math.atan2(abs(dx), dy)), 1)

    return angles


def _calculate_scores(angles: dict) -> dict:
    """各角度を理想範囲と比較し0-100のスコアを返す"""
    scores = {}
    for name, value in angles.items():
        if name not in IDEAL_RANGES:
            continue
        ideal_min, ideal_max, _ = IDEAL_RANGES[name]
        if ideal_min <= value <= ideal_max:
            scores[name] = 100
        elif value < ideal_min:
            scores[name] = max(0, round(100 - (ideal_min - value) * 2.5))
        else:
            scores[name] = max(0, round(100 - (value - ideal_max) * 2.5))
    return scores


def _draw_angle_overlay(image: np.ndarray, landmarks, angles: dict, shape) -> np.ndarray:
    """各関節の角度テキストをスケルトン画像にオーバーレイする"""
    h, w = shape[:2]
    result = image.copy()

    for name, lm_idx in _OVERLAY_MAP.items():
        if name not in angles:
            continue
        lm = landmarks[lm_idx]
        x = int(lm.x * w)
        y = int(lm.y * h)
        text = f"{angles[name]:.0f}\u00b0"

        # 黒背景付きテキストで視認性を確保
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(result, (x + 4, y - th - 8), (x + 4 + tw + 4, y - 2), (0, 0, 0), -1)
        cv2.putText(result, text, (x + 6, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    return result


def angles_to_text(angles: dict, scores: dict) -> str:
    """角度データとスコアをClaudeへのプロンプト用テキストに変換する"""
    lines = ["【姿勢データ（バイオメカニクス分析用）】"]
    for name, value in angles.items():
        if name not in IDEAL_RANGES:
            continue
        ideal_min, ideal_max, desc = IDEAL_RANGES[name]
        score = scores.get(name, "-")
        unit = "" if name == "体の傾き" else "°"
        ideal_unit = "" if name == "体の傾き" else "°"
        lines.append(
            f"- {name}: {value}{unit}　（理想: {ideal_min}-{ideal_max}{ideal_unit}、スコア: {score}/100）"
            + (f"　※{desc}" if desc else "")
        )
    overall = round(sum(scores.values()) / len(scores)) if scores else 0
    lines.append(f"\n総合スコア（参考）: {overall}/100")
    return "\n".join(lines)

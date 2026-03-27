import math
import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

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

# 角度テキストをオーバーレイする関節とそのランドマーク
_OVERLAY_MAP = {
    "右肘":   mp_pose.PoseLandmark.RIGHT_ELBOW,
    "左肘":   mp_pose.PoseLandmark.LEFT_ELBOW,
    "右膝":   mp_pose.PoseLandmark.RIGHT_KNEE,
    "左膝":   mp_pose.PoseLandmark.LEFT_KNEE,
    "右股関節": mp_pose.PoseLandmark.RIGHT_HIP,
    "左股関節": mp_pose.PoseLandmark.LEFT_HIP,
}


def analyze_pose(frame: np.ndarray) -> tuple[np.ndarray, dict | None, dict | None]:
    """
    フレームに姿勢推定とバイオメカニクス分析を適用する。
    戻り値: (角度オーバーレイ付きスケルトン画像, 関節角度データ, スコアデータ)
    姿勢が検出できない場合、角度とスコアはNone。
    """
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
        results = pose.process(frame)
        skeleton_frame = frame.copy()

        if not results.pose_landmarks:
            return skeleton_frame, None, None

        mp_drawing.draw_landmarks(
            skeleton_frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
        )

        lm = results.pose_landmarks.landmark
        angles = _calculate_angles(lm)
        scores = _calculate_scores(angles)
        annotated = _draw_angle_overlay(skeleton_frame, lm, angles, frame.shape)

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
    angles["右肘"] = _angle_3pts(
        lm[mp_pose.PoseLandmark.RIGHT_SHOULDER],
        lm[mp_pose.PoseLandmark.RIGHT_ELBOW],
        lm[mp_pose.PoseLandmark.RIGHT_WRIST],
    )
    angles["左肘"] = _angle_3pts(
        lm[mp_pose.PoseLandmark.LEFT_SHOULDER],
        lm[mp_pose.PoseLandmark.LEFT_ELBOW],
        lm[mp_pose.PoseLandmark.LEFT_WRIST],
    )

    # 膝（腰→膝→足首）
    angles["右膝"] = _angle_3pts(
        lm[mp_pose.PoseLandmark.RIGHT_HIP],
        lm[mp_pose.PoseLandmark.RIGHT_KNEE],
        lm[mp_pose.PoseLandmark.RIGHT_ANKLE],
    )
    angles["左膝"] = _angle_3pts(
        lm[mp_pose.PoseLandmark.LEFT_HIP],
        lm[mp_pose.PoseLandmark.LEFT_KNEE],
        lm[mp_pose.PoseLandmark.LEFT_ANKLE],
    )

    # 股関節（肩→腰→膝）
    angles["右股関節"] = _angle_3pts(
        lm[mp_pose.PoseLandmark.RIGHT_SHOULDER],
        lm[mp_pose.PoseLandmark.RIGHT_HIP],
        lm[mp_pose.PoseLandmark.RIGHT_KNEE],
    )
    angles["左股関節"] = _angle_3pts(
        lm[mp_pose.PoseLandmark.LEFT_SHOULDER],
        lm[mp_pose.PoseLandmark.LEFT_HIP],
        lm[mp_pose.PoseLandmark.LEFT_KNEE],
    )

    # 肩（左肩→右肩→右肘）
    angles["右肩"] = _angle_3pts(
        lm[mp_pose.PoseLandmark.LEFT_SHOULDER],
        lm[mp_pose.PoseLandmark.RIGHT_SHOULDER],
        lm[mp_pose.PoseLandmark.RIGHT_ELBOW],
    )

    # 肩ラインの傾き（左右肩のy座標差）
    angles["体の傾き"] = round(
        abs(
            lm[mp_pose.PoseLandmark.LEFT_SHOULDER].y
            - lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
        ) * 100,
        1,
    )

    # 体幹前傾（肩中点→腰中点のベクトルと垂直線の角度）
    s_mid_x = (lm[mp_pose.PoseLandmark.LEFT_SHOULDER].x + lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].x) / 2
    s_mid_y = (lm[mp_pose.PoseLandmark.LEFT_SHOULDER].y + lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].y) / 2
    h_mid_x = (lm[mp_pose.PoseLandmark.LEFT_HIP].x + lm[mp_pose.PoseLandmark.RIGHT_HIP].x) / 2
    h_mid_y = (lm[mp_pose.PoseLandmark.LEFT_HIP].y + lm[mp_pose.PoseLandmark.RIGHT_HIP].y) / 2
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

    for name, lm_id in _OVERLAY_MAP.items():
        if name not in angles:
            continue
        lm = landmarks[lm_id]
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

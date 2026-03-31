import mediapipe as mp
import numpy as np
import cv2
import urllib.request
import os

# モデルファイルは /tmp に保存（Streamlit Cloud でも書き込み可能）
MODEL_PATH = "/tmp/pose_landmarker_lite.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)

# 描画用ポーズコネクション（旧 POSE_CONNECTIONS の代替）
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


def analyze_pose(frame: np.ndarray) -> tuple[np.ndarray, dict | None]:
    """
    フレームに姿勢推定を適用する。
    戻り値: (スケルトン描画済み画像, 関節角度データ)
    姿勢が検出できない場合は角度データがNoneになる。
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
            return skeleton_frame, None

        landmarks = result.pose_landmarks[0]
        _draw_landmarks(skeleton_frame, landmarks)
        angles = _calculate_angles(landmarks)

    return skeleton_frame, angles


def _calculate_angles(landmarks) -> dict:
    """主要な関節角度を計算する（ユーザーには非表示・Claude入力専用）"""

    def angle(a, b, c) -> float:
        """3点から角度（度）を計算する。bが頂点。"""
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        ba = a - b
        bc = c - b
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        return round(float(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))), 1)

    lm = landmarks
    return {
        # インデックスは mediapipe の仕様に準拠
        "右肘": angle(lm[12], lm[14], lm[16]),  # RIGHT_SHOULDER→ELBOW→WRIST
        "左肘": angle(lm[11], lm[13], lm[15]),  # LEFT_SHOULDER→ELBOW→WRIST
        "右膝": angle(lm[24], lm[26], lm[28]),  # RIGHT_HIP→KNEE→ANKLE
        "左膝": angle(lm[23], lm[25], lm[27]),  # LEFT_HIP→KNEE→ANKLE
        "右肩": angle(lm[11], lm[12], lm[14]),  # LEFT_SHOULDER→RIGHT_SHOULDER→ELBOW
        "体の傾き": round(abs(lm[11].y - lm[12].y) * 100, 1),
    }


def angles_to_text(angles: dict) -> str:
    """角度データをClaudeへのプロンプト用テキストに変換する"""
    lines = ["【姿勢データ（参考値）】"]
    for name, value in angles.items():
        if name == "体の傾き":
            lines.append(f"- {name}: {value}（0に近いほど水平）")
        else:
            lines.append(f"- {name}: {value}°")
    return "\n".join(lines)

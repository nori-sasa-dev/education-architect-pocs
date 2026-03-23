import mediapipe as mp
import numpy as np
import cv2

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


def analyze_pose(frame: np.ndarray) -> tuple[np.ndarray, dict | None]:
    """
    フレームに姿勢推定を適用する。
    戻り値: (スケルトン描画済み画像, 関節角度データ)
    姿勢が検出できない場合は角度データがNoneになる。
    """
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
        results = pose.process(frame)

        # スケルトン描画用に元フレームをコピー
        skeleton_frame = frame.copy()

        if not results.pose_landmarks:
            return skeleton_frame, None

        # スケルトンを描画
        mp_drawing.draw_landmarks(
            skeleton_frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
        )

        # 関節角度を計算（Claude への入力用）
        angles = _calculate_angles(results.pose_landmarks.landmark)

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
        # 右肘（肩→肘→手首）
        "右肘": angle(
            lm[mp_pose.PoseLandmark.RIGHT_SHOULDER],
            lm[mp_pose.PoseLandmark.RIGHT_ELBOW],
            lm[mp_pose.PoseLandmark.RIGHT_WRIST],
        ),
        # 左肘
        "左肘": angle(
            lm[mp_pose.PoseLandmark.LEFT_SHOULDER],
            lm[mp_pose.PoseLandmark.LEFT_ELBOW],
            lm[mp_pose.PoseLandmark.LEFT_WRIST],
        ),
        # 右膝（腰→膝→足首）
        "右膝": angle(
            lm[mp_pose.PoseLandmark.RIGHT_HIP],
            lm[mp_pose.PoseLandmark.RIGHT_KNEE],
            lm[mp_pose.PoseLandmark.RIGHT_ANKLE],
        ),
        # 左膝
        "左膝": angle(
            lm[mp_pose.PoseLandmark.LEFT_HIP],
            lm[mp_pose.PoseLandmark.LEFT_KNEE],
            lm[mp_pose.PoseLandmark.LEFT_ANKLE],
        ),
        # 右肩（首→右肩→右肘）
        "右肩": angle(
            lm[mp_pose.PoseLandmark.LEFT_SHOULDER],
            lm[mp_pose.PoseLandmark.RIGHT_SHOULDER],
            lm[mp_pose.PoseLandmark.RIGHT_ELBOW],
        ),
        # 体の傾き（左肩と右肩のy座標差から推定）
        "体の傾き": round(
            abs(
                lm[mp_pose.PoseLandmark.LEFT_SHOULDER].y
                - lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
            )
            * 100,
            1,
        ),
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

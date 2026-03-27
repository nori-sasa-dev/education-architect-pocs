import cv2
import numpy as np
import tempfile
import os


def extract_frames(video_file) -> tuple[list[np.ndarray], float]:
    """
    動画ファイルからフレームを抽出する。
    戻り値: (フレームリスト, fps)
    """
    suffix = os.path.splitext(video_file.name)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(video_file.read())
        tmp_path = tmp.name

    cap = cv2.VideoCapture(tmp_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame_rgb)

    cap.release()
    os.unlink(tmp_path)

    return frames, fps


def frame_to_bytes(frame: np.ndarray) -> bytes:
    """numpy配列のフレームをPNG bytesに変換する"""
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode(".png", frame_bgr)
    return buf.tobytes()

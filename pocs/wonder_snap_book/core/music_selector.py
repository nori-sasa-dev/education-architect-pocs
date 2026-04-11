import os
import random

# BGMディレクトリ
BGM_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "bgm")


def get_bgm_path() -> str | None:
    """BGMファイルをランダムに選んでパスを返す。ファイルがない場合はNoneを返す"""
    if not os.path.exists(BGM_DIR):
        return None

    # MP3ファイルを探す
    bgm_files = [f for f in os.listdir(BGM_DIR) if f.endswith(".mp3")]
    if not bgm_files:
        return None

    selected = random.choice(bgm_files)
    return os.path.join(BGM_DIR, selected)

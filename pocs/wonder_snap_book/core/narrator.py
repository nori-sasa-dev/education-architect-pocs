import os
import io

# ElevenLabsのデフォルト音声ID（日本語対応音声）
DEFAULT_VOICE_ID = "cgSgspJ2msm6clMCkdW9"  # Rachel（落ち着いた女性の声）


def text_to_speech(text: str, elevenlabs_api_key: str = None, voice_id: str = None) -> bytes | None:
    """テキストを音声に変換してbytesで返す。APIキー未設定時はNoneを返す"""
    if not elevenlabs_api_key:
        # デモモード：音声なし
        return None

    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings

    client = ElevenLabs(api_key=elevenlabs_api_key)
    voice = voice_id or os.getenv("ELEVENLABS_VOICE_ID") or DEFAULT_VOICE_ID

    audio = client.text_to_speech.convert(
        voice_id=voice,
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.8,        # 安定した声（ゆれが少ない）
            similarity_boost=0.7,
            style=0.1,            # スタイルは控えめ（ストーリーを邪魔しない）
            use_speaker_boost=True,
        ),
    )

    # generatorをbytesに変換
    audio_bytes = io.BytesIO()
    for chunk in audio:
        audio_bytes.write(chunk)
    return audio_bytes.getvalue()

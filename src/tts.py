import logging
import time
import wave
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

MODEL = "gemini-2.5-flash-preview-tts"
SAMPLE_RATE = 24000
SAMPLE_WIDTH = 2  # 16bit
CHANNELS = 1

# リトライ対象とする一時的エラー
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(exc: Exception) -> bool:
    """リトライすべき一時的エラーかどうかを判定する。"""
    # google-genai の APIError 系
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status_code is not None and int(status_code) in _RETRYABLE_STATUS_CODES:
        return True
    # ネットワーク系
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    return False


def _save_wav(filepath: Path, pcm_data: bytes) -> None:
    """PCMデータをWAVファイルとして保存する。"""
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)


def _build_prompt(text: str, style_prompt: str) -> str:
    """テキストとスタイル指示からTTSプロンプトを構築する。"""
    parts = []
    if style_prompt:
        parts.append(style_prompt)
    parts.append(f"Read the following text aloud exactly as written:\n\n{text}")
    return "\n\n".join(parts)


def _extract_audio_data(response) -> bytes:
    """APIレスポンスから音声データを抽出し、検証する。"""
    if not response.candidates:
        raise ValueError("APIレスポンスに candidates が含まれていません")
    candidate = response.candidates[0]
    if not candidate.content or not candidate.content.parts:
        raise ValueError("APIレスポンスに音声データが含まれていません")
    part = candidate.content.parts[0]
    if not part.inline_data or not part.inline_data.data:
        raise ValueError("APIレスポンスの inline_data が空です")
    return part.inline_data.data


def create_client(api_key: str) -> genai.Client:
    """Gemini APIクライアントを生成する。"""
    return genai.Client(api_key=api_key)


def synthesize(
    text: str,
    client: genai.Client,
    voice_name: str = "Algieba",
    style_prompt: str = "",
    max_retries: int = 3,
) -> bytes:
    """テキストを音声データ(PCM)に変換する。リトライ付き。"""
    prompt = _build_prompt(text, style_prompt)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                ),
            )
            return _extract_audio_data(response)

        except Exception as e:
            if attempt < max_retries - 1 and _is_retryable(e):
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "API呼び出し失敗 (試行 %d/%d): %s  %d秒後にリトライ...",
                    attempt + 1,
                    max_retries,
                    e,
                    wait,
                )
                time.sleep(wait)
            else:
                raise


def synthesize_and_save(
    text: str,
    output_path: Path,
    client: genai.Client,
    voice_name: str = "Algieba",
    style_prompt: str = "",
) -> None:
    """テキストを音声合成し、WAVファイルとして保存する。"""
    pcm_data = synthesize(text, client, voice_name, style_prompt)
    _save_wav(output_path, pcm_data)

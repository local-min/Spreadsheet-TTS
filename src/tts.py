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


def _save_wav(filepath: Path, pcm_data: bytes) -> None:
    """PCMデータをWAVファイルとして保存する。"""
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)


def _build_prompt(text: str, style_prompt: str) -> str:
    """テキストとスタイル指示からTTSプロンプトを構築する。"""
    if style_prompt:
        return f"{style_prompt}\n\n{text}"
    return text


def synthesize(
    text: str,
    api_key: str,
    voice_name: str = "Algieba",
    style_prompt: str = "",
    max_retries: int = 3,
) -> bytes:
    """テキストを音声データ(PCM)に変換する。リトライ付き。"""
    client = genai.Client(api_key=api_key)
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
            data = response.candidates[0].content.parts[0].inline_data.data
            return data

        except Exception as e:
            if attempt < max_retries - 1:
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
    api_key: str,
    voice_name: str = "Algieba",
    style_prompt: str = "",
) -> None:
    """テキストを音声合成し、WAVファイルとして保存する。"""
    pcm_data = synthesize(text, api_key, voice_name, style_prompt)
    _save_wav(output_path, pcm_data)

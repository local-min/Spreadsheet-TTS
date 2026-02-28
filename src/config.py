import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config(config_path: str = "config.yaml") -> dict:
    """config.yamlを読み込み、環境変数と統合して返す。"""
    load_dotenv()

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Gemini APIキーを環境変数から取得
    env_var = config.get("auth", {}).get("gemini_api_key_env", "GEMINI_API_KEY")
    api_key = os.environ.get(env_var)
    if not api_key:
        raise ValueError(
            f"環境変数 {env_var} が設定されていません。"
            f".envファイルまたは環境変数にGemini APIキーを設定してください。"
        )
    config["auth"]["gemini_api_key"] = api_key

    # スプレッドシートIDを環境変数から取得（.envを優先、config.yamlにフォールバック）
    spreadsheet_id = os.environ.get("SPREADSHEET_ID", "").strip()
    if spreadsheet_id:
        config["google_sheets"]["spreadsheet_id"] = spreadsheet_id
    if not config["google_sheets"].get("spreadsheet_id"):
        raise ValueError(
            "スプレッドシートIDが設定されていません。"
            ".envファイルに SPREADSHEET_ID を設定してください。"
        )

    return config


def column_letter_to_index(letter: str) -> int:
    """列文字(A, B, C...)を0始まりのインデックスに変換する。"""
    letter = letter.upper()
    result = 0
    for char in letter:
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result - 1

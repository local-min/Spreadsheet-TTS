import argparse
import logging
import re
import sys
from pathlib import Path

from src.config import load_config
from src.sheets import fetch_texts
from src.tts import synthesize_and_save

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def sanitize_filename(text: str, max_chars: int = 20) -> str:
    """テキストからファイル名に使える文字列を生成する。"""
    # 改行・制御文字を除去
    clean = re.sub(r"[\n\r\t]", " ", text)
    # ファイル名に使えない文字を除去
    clean = re.sub(r'[\\/:*?"<>|]', "", clean)
    # 先頭のスペースを除去してトリム
    clean = clean.strip()[:max_chars]
    return clean


def parse_row_range(row_range: str) -> tuple[int | None, int | None]:
    """'1-10' 形式の行範囲を (start, end) に変換する。"""
    if "-" in row_range:
        parts = row_range.split("-", 1)
        start = int(parts[0]) if parts[0] else None
        end = int(parts[1]) if parts[1] else None
        return start, end
    else:
        row = int(row_range)
        return row, row


def main():
    parser = argparse.ArgumentParser(
        description="Google Sheetsのテキストを音声化するツール"
    )
    parser.add_argument(
        "--config", default="config.yaml", help="設定ファイルのパス (default: config.yaml)"
    )
    parser.add_argument("--voice", help="ボイス名を上書き指定")
    parser.add_argument("--output", help="出力ディレクトリを上書き指定")
    parser.add_argument("--rows", help="処理する行範囲 (例: 1-10)")
    parser.add_argument(
        "--dry-run", action="store_true", help="テキスト一覧を表示するのみ（API呼び出しなし）"
    )
    args = parser.parse_args()

    # 設定読み込み
    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        logger.error(e)
        sys.exit(1)

    # CLIオプションで上書き
    if args.voice:
        config["tts"]["voice_name"] = args.voice
    if args.output:
        config["output"]["directory"] = args.output
    if args.rows:
        start, end = parse_row_range(args.rows)
        if start is not None:
            config["google_sheets"]["start_row"] = start
        if end is not None:
            config["google_sheets"]["end_row"] = end

    # テキスト取得
    logger.info("Google Sheetsからテキストを取得中...")
    try:
        texts = fetch_texts(config)
    except Exception as e:
        logger.error("スプレッドシートの読み取りに失敗しました: %s", e)
        sys.exit(1)

    if not texts:
        logger.warning("対象テキストが見つかりませんでした。")
        sys.exit(0)

    logger.info("取得テキスト数: %d件", len(texts))

    # dry-runモード
    if args.dry_run:
        logger.info("=== Dry Run モード（API呼び出しなし） ===")
        for i, text in enumerate(texts, 1):
            preview = text[:50] + ("..." if len(text) > 50 else "")
            print(f"  [{i}/{len(texts)}] {preview}")
        sys.exit(0)

    # 出力ディレクトリ準備
    output_dir = Path(config["output"]["directory"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # TTS設定
    api_key = config["auth"]["gemini_api_key"]
    voice_name = config["tts"].get("voice_name", "Kore")
    style_prompt = config["tts"].get("style_prompt", "")
    prefix = config["output"].get("filename_prefix", "")
    max_chars = config["output"].get("filename_max_chars", 20)

    # 処理ループ
    success = 0
    failed = 0

    for i, text in enumerate(texts, 1):
        preview = text[:40] + ("..." if len(text) > 40 else "")
        logger.info("[%d/%d] 処理中: %s", i, len(texts), preview)

        # ファイル名生成
        name_part = sanitize_filename(text, max_chars)
        if prefix:
            filename = f"{prefix}_{i:03d}_{name_part}.wav"
        else:
            filename = f"{i:03d}_{name_part}.wav"
        output_path = output_dir / filename

        try:
            synthesize_and_save(text, output_path, api_key, voice_name, style_prompt)
            logger.info("  -> 保存: %s", output_path)
            success += 1
        except Exception as e:
            logger.error("  -> 失敗: %s", e)
            failed += 1

    # サマリー
    logger.info("=" * 40)
    logger.info("完了: 成功 %d件 / 失敗 %d件 / 合計 %d件", success, failed, len(texts))
    logger.info("出力先: %s", output_dir.resolve())


if __name__ == "__main__":
    main()

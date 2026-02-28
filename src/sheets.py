from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from .config import column_letter_to_index

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def fetch_texts(config: dict) -> list[str]:
    """Google Sheetsから指定列のテキスト一覧を取得する。"""
    sheets_config = config["google_sheets"]
    auth_config = config["auth"]

    # 認証
    key_path = Path(auth_config["service_account_key"])
    if not key_path.exists():
        raise FileNotFoundError(
            f"サービスアカウント鍵ファイルが見つかりません: {key_path}"
        )
    creds = Credentials.from_service_account_file(str(key_path), scopes=SCOPES)
    client = gspread.authorize(creds)

    # スプレッドシートを開く
    spreadsheet = client.open_by_key(sheets_config["spreadsheet_id"])

    # シート選択
    sheet_name = sheets_config.get("sheet_name", "")
    if sheet_name:
        worksheet = spreadsheet.worksheet(sheet_name)
    else:
        worksheet = spreadsheet.sheet1

    # 指定列のデータを取得
    col_index = column_letter_to_index(sheets_config.get("text_column", "A")) + 1
    all_values = worksheet.col_values(col_index)

    # 行範囲でスライス
    start_row = sheets_config.get("start_row", 2)
    end_row = sheets_config.get("end_row")

    # start_rowは1始まり → リストは0始まりなので -1
    start_idx = start_row - 1
    if end_row:
        values = all_values[start_idx:end_row]
    else:
        values = all_values[start_idx:]

    # 空行をフィルタリング
    texts = [v.strip() for v in values if v.strip()]

    return texts

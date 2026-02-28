import logging
import subprocess
from pathlib import Path

import google.auth
import gspread
from google.oauth2.service_account import Credentials

from .config import column_letter_to_index

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _get_gcloud_project() -> str | None:
    """gcloud CLI のデフォルトプロジェクトIDを取得する。"""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True, text=True, timeout=5,
        )
        project = result.stdout.strip()
        if result.returncode == 0 and project:
            return project
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _get_credentials(auth_config: dict):
    """認証情報を取得する。サービスアカウントキーがあればそちらを、なければADCを使用。"""
    key = auth_config.get("service_account_key", "")
    key_path = Path(key) if key else None

    if key_path and key_path.exists():
        logger.info("認証: サービスアカウントキー (%s)", key_path)
        return Credentials.from_service_account_file(str(key_path), scopes=SCOPES)

    logger.info("認証: Application Default Credentials (ADC)")
    creds, project = google.auth.default(scopes=SCOPES)

    # ADCユーザー認証ではクォータプロジェクトが必要
    if not getattr(creds, "quota_project_id", None):
        project = project or _get_gcloud_project()
        if project:
            creds = creds.with_quota_project(project)
            logger.info("クォータプロジェクト: %s", project)
        else:
            raise RuntimeError(
                "クォータプロジェクトが設定されていません。以下を実行してください:\n"
                "  gcloud auth application-default set-quota-project YOUR_PROJECT_ID"
            )

    return creds


def fetch_texts(config: dict) -> list[str]:
    """Google Sheetsから指定列のテキスト一覧を取得する。"""
    sheets_config = config["google_sheets"]
    auth_config = config["auth"]

    # 認証
    creds = _get_credentials(auth_config)
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
    if end_row is not None:
        values = all_values[start_idx:end_row]
    else:
        values = all_values[start_idx:]

    # 空行をフィルタリング
    texts = [v.strip() for v in values if v.strip()]

    return texts

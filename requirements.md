# 要件定義書: スプレッドシート音声化システム

## 1. プロジェクト概要

Google Sheetsに記載されたテキストを、Gemini 2.5 Pro Preview TTS APIを使って音声ファイル（WAV）に変換するCLIシステム。

## 2. システム構成図

```
Google Sheets  →  Python Script  →  Gemini TTS API  →  WAV Files
  (入力)           (処理)              (音声合成)        (出力)
```

## 3. 技術スタック

| 項目 | 技術 |
|------|------|
| 言語 | Python 3.10+ |
| TTS API | Gemini 2.5 Pro Preview TTS (`gemini-2.5-pro-preview-tts`) |
| SDK | `google-genai` (Google Gen AI Python SDK) |
| スプレッドシート連携 | `gspread` + Google Sheets API |
| 認証 | Google Service Account (JSON鍵ファイル) |
| 出力形式 | WAV (PCM 24000Hz, 16bit, mono) |

## 4. 機能要件

### 4.1 スプレッドシート読み取り

| 項目 | 内容 |
|------|------|
| データソース | Google Sheets |
| 認証方式 | サービスアカウントのJSON鍵ファイル |
| シート構成 | テキスト列のみ（1列にテキスト行が並ぶ） |
| 対象列 | 設定ファイル or CLIオプションで指定可能（デフォルト: A列） |
| 空行処理 | スキップする |
| 先頭行処理 | ヘッダー行として除外可能（オプション） |

### 4.2 音声合成（TTS）

| 項目 | 内容 |
|------|------|
| モデル | `gemini-2.5-pro-preview-tts` |
| スピーカー | シングルスピーカー |
| 言語 | 日本語 |
| 音声（ボイス） | 30種類のプリセットボイスから選択可能 |
| デフォルトボイス | `Kore`（Firm）※後述のボイス一覧から変更可能 |
| スタイル指示 | プロンプトで速度・トーン・スタイルを指定可能 |
| 入力トークン上限 | 8,192トークン（長文は自動分割を検討） |

#### 利用可能ボイス一覧（30種類）

| ボイス名 | 特徴 | ボイス名 | 特徴 |
|----------|------|----------|------|
| Zephyr | Bright | Puck | Upbeat |
| Charon | Informative | Kore | Firm |
| Fenrir | Excitable | Leda | Youthful |
| Orus | Firm | Aoede | Breezy |
| Callirrhoe | Easy-going | Autonoe | Bright |
| Enceladus | Breathy | Iapetus | Clear |
| Umbriel | Easy-going | Algieba | Smooth |
| Despina | Smooth | Erinome | Clear |
| Algenib | Gravelly | Rasalgethi | Informative |
| Laomedeia | Upbeat | Achernar | Soft |
| Alnilam | Firm | Schedar | Even |
| Gacrux | Mature | Pulcherrima | Forward |
| Achird | Friendly | Zubenelgenubi | Casual |
| Vindemiatrix | Gentle | Sadachbia | Lively |
| Sadaltager | Knowledgeable | Sulafat | Warm |

### 4.3 出力

| 項目 | 内容 |
|------|------|
| 形式 | WAV (PCM) |
| サンプルレート | 24,000 Hz |
| ビット深度 | 16bit |
| チャンネル | モノラル |
| ファイル命名規則 | `{連番}_{先頭N文字}.wav`（例: `001_こんにちは.wav`）|
| 出力先 | 指定ディレクトリ（デフォルト: `./output/`）|

## 5. 設定・CLI仕様

### 5.1 設定ファイル（`config.yaml`）

```yaml
# Google Sheets設定
google_sheets:
  spreadsheet_id: "YOUR_SPREADSHEET_ID"
  sheet_name: "Sheet1"          # シート名（デフォルト: 最初のシート）
  text_column: "A"              # テキストが入っている列
  start_row: 2                  # 開始行（1=ヘッダー含む, 2=ヘッダー除外）
  end_row: null                 # 終了行（null=最終行まで）

# TTS設定
tts:
  voice_name: "Kore"            # ボイス名
  style_prompt: ""              # スタイル指示（例: "落ち着いたトーンで読んでください"）

# 出力設定
output:
  directory: "./output"         # 出力ディレクトリ
  filename_prefix: ""           # ファイル名のプレフィックス
  filename_max_chars: 20        # ファイル名に含めるテキストの最大文字数

# 認証
auth:
  service_account_key: "./credentials.json"   # サービスアカウント鍵
  gemini_api_key_env: "GEMINI_API_KEY"        # Gemini API Key環境変数名
```

### 5.2 CLIインターフェース

```bash
# 基本実行
python main.py

# オプション指定
python main.py --config config.yaml
python main.py --voice Puck
python main.py --output ./my_output
python main.py --rows 1-10          # 行範囲指定
python main.py --dry-run            # テキスト一覧確認のみ（API呼び出しなし）
```

## 6. 処理フロー

```
1. 設定ファイル読み込み / CLI引数パース
2. Google Sheets認証・接続
3. 指定シート・列からテキスト行を取得
4. 空行をフィルタリング
5. テキストごとにループ:
   a. テキストがトークン上限を超える場合 → 警告ログを出力しスキップ
   b. Gemini TTS APIにリクエスト送信
   c. レスポンスのPCMデータをWAVファイルとして保存
   d. 進捗をコンソールに表示（例: [3/25] 処理中...）
6. 完了サマリーを出力（成功数 / 失敗数 / 合計）
```

## 7. エラーハンドリング

| エラー種別 | 対処 |
|-----------|------|
| API認証エラー | エラーメッセージを表示して終了 |
| スプレッドシートアクセスエラー | エラーメッセージを表示して終了 |
| APIレート制限 | リトライ（最大3回、指数バックオフ） |
| テキストが長すぎる | 警告ログを出力しスキップ、次の行へ進む |
| 個別行のAPI失敗 | エラーログ出力、次の行へ進む（全体は中断しない） |
| 出力ディレクトリなし | 自動作成 |

## 8. ディレクトリ構成

```
spreadsheet-tts/
├── main.py                # エントリーポイント
├── config.yaml            # 設定ファイル
├── requirements.txt       # Python依存パッケージ
├── credentials.json       # Google Service Account鍵（gitignore対象）
├── src/
│   ├── __init__.py
│   ├── sheets.py          # Google Sheets読み取りモジュール
│   ├── tts.py             # Gemini TTS APIモジュール
│   └── config.py          # 設定読み込みモジュール
├── output/                # 音声ファイル出力先
│   └── .gitkeep
├── .env                   # 環境変数（GEMINI_API_KEY）
└── .gitignore
```

## 9. 必要な認証情報・事前準備

### 9.1 Gemini API Key
1. Google AI Studio (https://aistudio.google.com/apikey) でAPIキーを取得
2. 環境変数 `GEMINI_API_KEY` に設定、または `.env` ファイルに記載

### 9.2 Google Sheets API（サービスアカウント）
1. Google Cloud ConsoleでプロジェクトのGoogle Sheets APIを有効化
2. サービスアカウントを作成し、JSON鍵ファイルをダウンロード
3. 対象スプレッドシートをサービスアカウントのメールアドレスに共有
4. `credentials.json` としてプロジェクトルートに配置

## 10. 依存パッケージ

```
google-genai          # Gemini API SDK
gspread               # Google Sheets操作
google-auth           # Google認証
pyyaml                # YAML設定ファイル読み込み
python-dotenv         # .env環境変数読み込み
```

## 11. 制約事項・注意点

| 項目 | 内容 |
|------|------|
| トークン上限 | 入力: 8,192トークン / 出力: 16,384トークン |
| API料金 | Gemini API の従量課金が発生（利用量に注意） |
| レート制限 | APIのレート制限に準拠（リトライロジックで対応） |
| ボイス品質 | Pro TTS はスタジオ品質の音声生成に対応 |
| 日本語対応 | Gemini TTS は日本語 (ja) をサポート済み |
| プレビュー版 | モデルはpreview版のため、仕様変更の可能性あり |

## 12. 将来的な拡張案（スコープ外）

- MP3変換オプション（ffmpeg連携）
- マルチスピーカー対応（話者列の追加）
- バッチ処理の並列化
- Web UI（Streamlit等）
- 長文テキストの自動分割＋結合
- 進捗のスプレッドシートへの書き戻し

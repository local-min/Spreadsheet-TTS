# Spreadsheet TTS

Google Sheetsに記載されたテキストを **Gemini TTS API** で自然な音声ファイル（WAV）に自動変換するPythonツールです。

```
Google Sheets  →  Python Script  →  Gemini TTS API  →  WAV Files
  (テキスト)        (自動処理)         (音声合成)        (音声出力)
```

| 項目 | 内容 |
|------|------|
| TTSモデル | `gemini-2.5-flash-preview-tts` |
| ボイス | Algieba（Smooth） |
| 出力形式 | WAV（24kHz / 16bit / モノラル） |
| 言語 | 日本語 |

## 事前準備

- Python 3.10 以上
- [uv](https://docs.astral.sh/uv/)
- [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install)
- Google アカウント
- Gemini API キー

## セットアップ

### 1. Gemini API キーの取得

1. [Google AI Studio](https://aistudio.google.com/apikey) にアクセス
2. 「APIキーを作成」をクリック
3. 表示されたAPIキーをコピーして控えておく

### 2. Google Sheets API の有効化と認証

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 上部の「プロジェクトを選択」→「**新しいプロジェクト**」→ 任意の名前で作成
3. 左メニュー「**APIとサービス**」→「**ライブラリ**」
   - 「Google Sheets API」を検索 → **有効にする**
4. ターミナルで ADC（Application Default Credentials）認証を実行

```bash
# Sheets APIスコープ付きでログイン（ブラウザが開きます）
gcloud auth application-default login \
  --scopes="openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/spreadsheets.readonly"

# クォータプロジェクトの設定（API利用枠の紐付け）
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

> `YOUR_PROJECT_ID` は手順2で作成したプロジェクトのIDに置き換えてください。

> **補足**: サービスアカウントキーを使う場合は、キーファイルのパスを `config.yaml` の `auth.service_account_key` に設定してください。ADC より優先されます。

### 3. プロジェクトのセットアップ

```bash
# 依存パッケージのインストール
uv sync

# 環境変数の設定
cp .env.example .env
# .env を編集して GEMINI_API_KEY を設定
```

### 4. config.yaml の編集

スプレッドシートIDを設定します。

```yaml
google_sheets:
  spreadsheet_id: "あなたのスプレッドシートID"
```

> **スプレッドシートIDの確認方法**: スプレッドシートのURL
> `https://docs.google.com/spreadsheets/d/【ここがID】/edit`

### 5. スプレッドシートの準備

A列にテキストを入力します（1行目はヘッダーとして除外されます）。

| | A |
|---|---|
| 1 | テキスト（ヘッダー） |
| 2 | こんにちは。今日の講義を始めます。 |
| 3 | 次のスライドをご覧ください。 |

## 使い方

```bash
# テスト実行（API呼び出しなし）
uv run python main.py --dry-run

# 本番実行
uv run python main.py

# ボイスを変更して実行
uv run python main.py --voice Puck

# 出力先を変更
uv run python main.py --output ./my_audio

# 行範囲を指定（2行目〜5行目のみ）
uv run python main.py --rows 2-5

# 設定ファイルを指定
uv run python main.py --config my_config.yaml
```

`./output/` フォルダにWAVファイルが生成されます。

## カスタマイズ

### config.yaml のデフォルト設定

```yaml
# Google Sheets設定
google_sheets:
  spreadsheet_id: "あなたのスプレッドシートID"
  sheet_name: ""                # シート名（空=最初のシート）
  text_column: "A"              # テキストが入っている列
  start_row: 2                  # 開始行（2=ヘッダー除外）
  end_row: null                 # 終了行（null=最終行まで）

# TTS設定
tts:
  voice_name: "Algieba"          # ボイス名
  style_prompt: "Speak as a calm, professional corporate trainer. Use a measured pace with clear articulation. Maintain a warm but authoritative tone. Pause slightly before key concepts."

# 出力設定
output:
  directory: "./output"
  filename_prefix: ""
  filename_max_chars: 20

# 認証
auth:
  service_account_key: ""           # 空=ADCを使用 / パス指定=サービスアカウントキー
  gemini_api_key_env: "GEMINI_API_KEY"
```

### 利用可能なボイス一覧（30種類）

| ボイス名 | 特徴 | ボイス名 | 特徴 |
|----------|------|----------|------|
| Zephyr | Bright | Puck | Upbeat |
| Charon | Informative | **Kore** | **Firm** |
| Fenrir | Excitable | Leda | Youthful |
| Orus | Firm | Aoede | Breezy |
| Callirrhoe | Easy-going | Autonoe | Bright |
| Enceladus | Breathy | Iapetus | Clear |
| Umbriel | Easy-going | **Algieba** | **Smooth** |
| Despina | Smooth | Erinome | Clear |
| Algenib | Gravelly | Rasalgethi | Informative |
| Laomedeia | Upbeat | Achernar | Soft |
| Alnilam | Firm | Schedar | Even |
| Gacrux | Mature | Pulcherrima | Forward |
| Achird | Friendly | Zubenelgenubi | Casual |
| Vindemiatrix | Gentle | Sadachbia | Lively |
| Sadaltager | Knowledgeable | Sulafat | Warm |

### Style Prompt の例

```yaml
# 落ち着いた企業研修講師
style_prompt: "Speak as a calm, professional corporate trainer. Use a measured pace with clear articulation. Maintain a warm but authoritative tone. Pause slightly before key concepts."

# ニュースキャスター風
style_prompt: "はきはきとしたニュースキャスターのように、明瞭に読んでください。"

# 優しいナレーション
style_prompt: "穏やかで優しいトーンで、ゆっくりと語りかけるように読んでください。"
```

## トラブルシューティング

| エラー | 原因と対処 |
|--------|-----------|
| `環境変数 GEMINI_API_KEY が設定されていません` | `.env` ファイルにAPIキーが正しく記載されていない |
| `Could not automatically determine credentials` | `gcloud auth application-default login` を実行する |
| `Requested entity was not found` | スプレッドシートIDが間違っている or 自分のアカウントにアクセス権がない |
| `APIレート制限エラー` | 自動リトライ（最大3回）される。頻発する場合は間隔を空ける |

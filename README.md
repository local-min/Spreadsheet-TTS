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
- Google アカウント
- Gemini API キー
- Google Cloud サービスアカウント（Sheets読み取り用）

## セットアップ

### 1. Gemini API キーの取得

1. [Google AI Studio](https://aistudio.google.com/apikey) にアクセス
2. 「APIキーを作成」をクリック
3. 表示されたAPIキーをコピーして控えておく

### 2. Google Cloud サービスアカウントの作成

Google Sheetsにプログラムからアクセスするための認証情報です。

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 上部の「プロジェクトを選択」→「**新しいプロジェクト**」→ 任意の名前で作成
3. 左メニュー「**APIとサービス**」→「**ライブラリ**」
   - 「Google Sheets API」を検索 → **有効にする**
4. 左メニュー「**APIとサービス**」→「**認証情報**」
   - 「**＋認証情報を作成**」→「**サービスアカウント**」を選択
   - 名前を入力（例: `spreadsheet-tts`）→ 作成
5. 作成したサービスアカウントをクリック
   - 「**鍵**」タブ →「**鍵を追加**」→「**新しい鍵を作成**」→ **JSON** を選択
   - JSONファイルが自動ダウンロードされる
6. JSONファイル内の `client_email`（例: `xxx@project.iam.gserviceaccount.com`）をコピー
7. 対象の **Google スプレッドシート** を開き、共有ボタンから **そのメールアドレスに「閲覧者」として共有**

> **注意**: 「OAuthクライアントID」ではなく「**サービスアカウント**」を選んでください

### 3. プロジェクトのセットアップ

```bash
# 依存パッケージのインストール
uv sync

# サービスアカウント鍵の配置
cp ~/Downloads/ダウンロードしたファイル名.json ./credentials.json

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
  service_account_key: "./credentials.json"
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
| `サービスアカウント鍵ファイルが見つかりません` | `credentials.json` がプロジェクトルートにない |
| `missing fields token_uri, client_email` | OAuthクライアントIDの鍵を使っている → **サービスアカウント**の鍵を作り直す |
| `Requested entity was not found` | スプレッドシートIDが間違っている or サービスアカウントに共有されていない |
| `APIレート制限エラー` | 自動リトライ（最大3回）される。頻発する場合は間隔を空ける |

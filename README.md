# personal-agent

チャットで話しかけるだけで、Redmineのタスク管理・スケジュール調整・情報収集を代行するパーソナルAIエージェントです。

## 概要

手作業・アナログな業務をデジタル化・自動化することを目的に開発した個人向けAIアシスタントシステムです。
自然言語でエージェントに指示するだけで、Redmineへのタスク登録・検索・更新・優先度調整を実行します。

### こんなことができます

```
「設計書レビューのタスクを高優先度で来週金曜までに作って」
→ Redmine にチケットを自動登録

「今日のタスクを教えて」
→ 本日締め切りのタスク一覧を返答

「#123 を完了にして、コメントに『初回レビュー完了』と書いて」
→ チケットのステータス更新 + コメント追加

「今週の優先タスクを整理してレポートして」
→ 期日・優先度の分析結果を提案
```

---

## 機能一覧

### フェーズ1（初期リリース）

| 機能 | 説明 |
|------|------|
| Redmine タスク作成 | 自然言語入力から Redmine チケットを自動登録 |
| Redmine タスク検索・一覧表示 | 条件指定でタスクを絞り込み・一覧取得 |
| Redmine タスク更新・進捗報告 | ステータス変更・進捗率・コメント追加 |
| タスク優先度・スケジュール調整 | 優先度変更・期日変更・対応順序の提案 |
| チャット UI | 自然言語でエージェントに指示する画面 |
| タスク一覧ダッシュボード | Redmine タスクをステータス別に可視化 |

### フェーズ2（追加予定）

| 機能 | 説明 |
|------|------|
| メモ・情報収集 | ウェブ検索・情報整理の代行 |
| 予定・カレンダー管理 | スケジュール確認・登録の支援 |
| 文書作成・編集支援 | レポート・メールの草案作成 |

---

## アーキテクチャ

```
┌──────────────────────────────────────────┐
│               ローカルPC                   │
│                                          │
│  ┌─────────────────┐  HTTP   ┌─────────────────────┐
│  │   Next.js UI    │ ──────→ │  Python Backend     │
│  │  チャット画面    │ ←────── │  (LangGraph Agent)  │
│  │  ダッシュボード  │         │  Port: 8000         │
│  │  Port: 3000     │         └──────────┬──────────┘
│  └─────────────────┘                    │ MCP
│                                ┌────────▼────────┐
│                                │  Redmine        │
│                                │  (Docker)       │
│                                │  Port: 8080     │
│                                └─────────────────┘
└──────────────────────────────────────────┘
                      │ HTTPS
            ┌─────────▼──────────┐
            │  Anthropic Claude  │
            │  API（外部）        │
            └────────────────────┘
```

---

## 技術スタック

| レイヤ | 技術 | 役割 |
|--------|------|------|
| フロントエンド | **Next.js** (Node.js 18+) | チャットUI・タスクダッシュボード |
| バックエンド | **Python 3.11+** + **LangGraph** | エージェントのワークフロー・状態管理 |
| タスク管理 | **Redmine** (Docker) | チケット管理基盤 |
| 連携プロトコル | **MCP** (Model Context Protocol) | エージェント↔Redmine のAPI連携 |
| AIモデル | **Anthropic Claude API** | 自然言語処理・ツール呼び出し判断 |

---

## セットアップ

### 必要条件

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Python | 3.11+ | バックエンド実行環境 |
| Node.js | 18+ | フロントエンド実行環境 |
| Docker / Docker Compose | 最新版 | Redmine・PostgreSQL の起動 |
| Anthropic API キー | - | Claude API 呼び出し |

---

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd personal-agent
```

---

### 2. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、以下の内容を記入してください。

```bash
# .env
# Anthropic Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key

# Redmine
REDMINE_URL=http://localhost:8080
REDMINE_API_KEY=your_redmine_api_key

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/personal_agent
```

> **注意**: `.env` ファイルには機密情報が含まれます。Git にコミットしないでください（`.gitignore` 設定済み）。

---

### 3. Redmine・PostgreSQL の起動

Docker Compose で Redmine と PostgreSQL を起動します。

```bash
docker compose up -d
```

起動確認:

```bash
docker compose ps
```

Redmine が起動したら `http://localhost:8080` にアクセスし、初期設定を行います。

**Redmine API キーの取得手順:**

1. `http://localhost:8080` にログイン（初期アカウント: `admin` / `admin`）
2. 右上のアカウントメニュー → **「個人設定」** を開く
3. **「APIアクセスキー」** を表示してコピー
4. コピーしたキーを `.env` の `REDMINE_API_KEY` に設定する

---

### 4. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成・有効化（推奨）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# DBマイグレーション
alembic upgrade head

# バックエンドの起動
uvicorn app.main:app --reload --port 8000
```

---

### 5. フロントエンドのセットアップ

別ターミナルで実行してください。

```bash
cd frontend

# 依存パッケージのインストール
npm install

# フロントエンドの起動
npm run dev
```

---

### 6. 動作確認

すべてのサービスが起動したら以下の URL にアクセスして確認します。

| サービス | URL | 説明 |
|---------|-----|------|
| チャット UI | http://localhost:3000 | エージェントとの会話画面 |
| ダッシュボード | http://localhost:3000/dashboard | タスク一覧・可視化 |
| バックエンド API | http://localhost:8000/docs | FastAPI 自動生成 API ドキュメント |
| Redmine | http://localhost:8080 | タスク管理画面 |

---

### テストの実行

**バックエンド:**

```bash
cd backend
pytest
# カバレッジレポート付き
pytest --cov=app --cov-report=term-missing
```

**フロントエンド:**

```bash
cd frontend
npm test
# カバレッジレポート付き
npm run test:coverage
```

---

## ドキュメント

要件定義書は [`docs/REQ/`](./docs/REQ/) 以下に格納しています。

| ドキュメント | 内容 |
|-----------|------|
| [REQ-001 プロジェクト概要書](./docs/REQ/REQ-001_プロジェクト概要書.md) | システム概要・目的・アーキテクチャ |
| [REQ-002 ビジネス要件定義書](./docs/REQ/REQ-002_ビジネス要件定義書.md) | ビジネス目標・課題・フェーズ定義 |
| [REQ-003 機能要件定義書](./docs/REQ/REQ-003_機能要件定義書.md) | 機能一覧・詳細要件 |
| [REQ-004 非機能要件定義書](./docs/REQ/REQ-004_非機能要件定義書.md) | 性能・拡張性・セキュリティ要件 |
| [REQ-005 ユースケース一覧・記述書](./docs/REQ/REQ-005_ユースケース一覧・記述書.md) | ユースケース詳細フロー |
| [REQ-006 ドメインモデル・ユビキタス言語集](./docs/REQ/REQ-006_ドメインモデル・ユビキタス言語集.md) | 用語定義・エンティティ設計 |
| [REQ-007 システム境界・外部IF定義](./docs/REQ/REQ-007_システム境界・外部インターフェース定義.md) | API仕様・外部連携仕様 |
| [REQ-008 制約・前提条件・リスク管理表](./docs/REQ/REQ-008_制約・前提条件・リスク管理表.md) | 制約・リスクと対策 |

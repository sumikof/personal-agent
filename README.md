# personal-agent

タスク管理・調整・各種作業依頼を幅広くこなすパーソナルエージェントです。

## 概要

日常的なタスク管理から作業の調整・依頼まで、様々なユースケースに対応するAIエージェントシステムです。

## 技術スタック

### バックエンド

- **Python** - メイン開発言語
- **LangGraph** - エージェントのワークフロー・状態管理フレームワーク

### フロントエンド

- **Next.js** - UIフレームワーク

### タスク管理

- **Redmine** - タスク管理ツール
- **MCP (Model Context Protocol)** - RedmineとエージェントのAPI連携

## 主な機能

- タスクの作成・更新・管理（Redmine連携）
- 作業の調整・スケジューリング
- 各種作業依頼の受付・実行
- MCPを通じたRedmineとのシームレスな連携

## アーキテクチャ

```
┌─────────────────┐      ┌──────────────────┐
│   Next.js UI    │ ←──→ │  LangGraph Agent │
└─────────────────┘      └────────┬─────────┘
                                  │ MCP
                          ┌───────▼────────┐
                          │    Redmine     │
                          └────────────────┘
```

## セットアップ

### 必要条件

- Python 3.11+
- Node.js 18+
- Redmineサーバー

### インストール

```bash
# バックエンド
pip install -r requirements.txt

# フロントエンド
cd frontend
npm install
```

### 環境変数

```env
REDMINE_URL=http://your-redmine-server
REDMINE_API_KEY=your_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 起動

```bash
# バックエンド（エージェント）
python main.py

# フロントエンド
cd frontend
npm run dev
```

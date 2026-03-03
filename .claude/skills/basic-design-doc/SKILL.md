---
name: basic-design-doc
description: |
  ウォーターフォール開発の基本設計（BSD）フェーズのドキュメントを作成するスキル。要件定義（REQ）フェーズのドキュメントを入力として読み込み、BSD-001〜BSD-008 の各基本設計書を生成・保存する。以下の場合に使用する。(1)「基本設計書を作成して」「BSD-XXX を書いて」と依頼された場合。(2) REQドキュメントを元に設計書を作成する場合。(3) システムアーキテクチャ・セキュリティ・画面設計・業務フロー・API設計・DB設計・外部IF設計・テスト計画のいずれかの基本設計書作成を依頼された場合。プロジェクトディレクトリは /home/ubuntu/workspace/Waterfall/ を想定。
context: fork
agent: agents/basic-design-doc.md
---

# 基本設計書（BSD）作成スキル

## パラメータ

| パラメータ | 説明 | 例 |
|---|---|---|
| PROJECT_ID | プロジェクトID | PRJ-001 |
| PROJECT_NAME | プロジェクト名 | initial-build |

## エージェント起動

このスキルは以下のサブエージェントを使用して作業を実行する。

| サブエージェント | タイプ | プロンプト |
|---|---|---|
| BSD 実行エージェント | general-purpose | `agents/basic-design-doc.md` |

### 起動手順

1. `agents/basic-design-doc.md` を Read で読み込む
2. `{{PROJECT_ID}}`, `{{PROJECT_NAME}}` を実際の値に置換する
3. 以下の形式で Task ツールを呼び出してサブエージェントを起動する

> **重要**: このスキルの作業はすべてサブエージェントに委譲する。マスターエージェントが直接実行してはならない。

Task ツール呼び出し:
- `subagent_type`: `"general-purpose"`
- `description`: `"BSD 基本設計実行"`
- `prompt`: 置換済みの agents/basic-design-doc.md の内容全文
- `context`: `"fork"`

## ドキュメント対応表

| ドキュメントID | ドキュメント名 | 入力元 | 保存先 |
|---|---|---|---|
| BSD-001 | システムアーキテクチャ設計書 | REQ-001, REQ-005, REQ-006 | `docs/BSD/BSD-001_architecture.md` |
| BSD-002 | セキュリティ基本設計書 | REQ-006 | `docs/BSD/BSD-002_security-design.md` |
| BSD-003 | 画面設計書（ワイヤーフレーム） | REQ-003, REQ-004 | `docs/BSD/BSD-003_screen-design.md` |
| BSD-004 | 業務フロー設計書 | REQ-002, REQ-003 | `docs/BSD/BSD-004_business-flow.md` |
| BSD-005 | API基本設計書 | REQ-003, REQ-005, REQ-007 | `docs/BSD/BSD-005_api-design.md` |
| BSD-006 | データベース基本設計書 | REQ-005, REQ-007 | `docs/BSD/BSD-006_database-design.md` |
| BSD-007 | 外部インターフェース基本設計書 | REQ-007 | `docs/BSD/BSD-007_external-interface-design.md` |
| BSD-008 | テスト計画書（基本） | REQ-006 | `projects/PRJ-{NNN}_{名称}/BSD/BSD-008_test-plan.md` |
| BSD-009 | ドメインモデル設計書（DDD 戦略設計） | REQ-002, REQ-003, REQ-005, REQ-008 | `docs/BSD/BSD-009_domain-model.md` |
| BSD-010 | データアーキテクチャ設計書 | REQ-005, REQ-006, REQ-007, BSD-006, BSD-009 | `docs/BSD/BSD-010_data-architecture.md` |

## REQドキュメントのパス

| ドキュメントID | パス |
|---|---|
| REQ-001 | `projects/PRJ-{NNN}_{名称}/REQ/REQ-001_system-requirements.md` |
| REQ-002 | `projects/PRJ-{NNN}_{名称}/REQ/REQ-002_business-requirements.md` |
| REQ-003 | `projects/PRJ-{NNN}_{名称}/REQ/REQ-003_use-cases.md` |
| REQ-004 | `projects/PRJ-{NNN}_{名称}/REQ/REQ-004_screen-list.md` |
| REQ-005 | `docs/REQ/REQ-005_feature-list.md` |
| REQ-006 | `docs/REQ/REQ-006_non-functional-requirements.md` |
| REQ-007 | `docs/REQ/REQ-007_external-interfaces.md` |
| REQ-008 | `docs/REQ/REQ-008_glossary.md` |

## 作業ワークフロー

### Step 1: 対象ドキュメントの特定

ユーザーのリクエストから作成対象のBSDドキュメントを特定する。複数指定・「全て」の場合は以下の生成順序で処理する。

**生成順序**: `BSD-001 → BSD-002 → BSD-003 → BSD-004 → BSD-009 → BSD-005 → BSD-006 → BSD-010 → BSD-007 → BSD-008`

> BSD-009 は BSD-004 の業務フロー情報が必要。BSD-010 は BSD-006 のテーブル構造と BSD-009 のコンテキスト定義が必要。

### Step 2: 入力REQドキュメントの読み込み

上記対応表の「入力元」に記載されたREQドキュメントをすべてReadツールで読み込む。ファイルが存在しない場合はユーザーに確認する。

プロジェクトフォルダが複数ある場合は、対象プロジェクトをユーザーに確認する（`projects/` 配下のフォルダ一覧を表示する）。

### Step 3: テンプレート参照

作成するBSDドキュメントに対応するテンプレートファイルを読み込む:

| 作成対象 | テンプレートファイル |
|---|---|
| BSD-001 | `references/bsd-001-architecture.md` |
| BSD-002 | `references/bsd-002-security.md` |
| BSD-003 | `references/bsd-003-screen-design.md` |
| BSD-004 | `references/bsd-004-business-flow.md` |
| BSD-005 | `references/bsd-005-api-design.md` |
| BSD-006 | `references/bsd-006-database-design.md` |
| BSD-007 | `references/bsd-007-external-interface.md` |
| BSD-008 | `references/bsd-008-test-plan.md` |
| BSD-009 | `references/bsd-009-domain-model.md` |
| BSD-010 | `references/bsd-010-data-architecture.md` |

### Step 4: ドキュメント生成

テンプレートのセクション構成に従い、REQドキュメントの内容を基にドキュメントを生成する。

**生成ルール:**
- テンプレートのセクション見出しを維持し、REQ内容から具体的な値を記載する
- REQに該当情報がない場合は `（要確認）` と記載し、空欄にしない
- ドキュメント冒頭に必ず **メタデータヘッダー** を記載する（後述）
- 用語はREQ-008（用語定義書）に従う（ファイルが存在する場合）

**メタデータヘッダー形式:**
```markdown
# {ドキュメント名}

| 項目 | 値 |
|---|---|
| ドキュメントID | BSD-{NNN} |
| バージョン | 1.0 |
| 作成日 | {今日の日付} |
| 入力元 | {REQ-XXX, REQ-YYY} |
| ステータス | 初版 |

---
```

### Step 5: ファイル保存

Writeツールで対応表の「保存先」パスに保存する。保存先ディレクトリが存在しない場合は事前に `mkdir -p` で作成する。

保存後、ファイルパスとドキュメントIDをユーザーに報告する。

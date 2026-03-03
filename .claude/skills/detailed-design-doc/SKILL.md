---
name: detailed-design-doc
description: |
  ウォーターフォール開発の詳細設計（DSD）フェーズのドキュメントを作成するスキル。基本設計（BSD）・要件定義（REQ）フェーズのドキュメントを入力として読み込み、機能ID（FEAT-NNN）単位でDSD-001〜DSD-008の各詳細設計書を生成・保存する。以下の場合に使用する。(1)「詳細設計書を作成して」「DSD-XXX を書いて」と依頼された場合。(2) FEAT-NNN の詳細設計書を作成する場合。(3) バックエンド詳細設計・フロントエンド詳細設計・API詳細設計・DB詳細設計・外部IF詳細設計・バッチ処理詳細設計・コーディング規約・単体テスト設計のいずれかを依頼された場合。プロジェクトディレクトリは /home/ubuntu/workspace/Waterfall/ を想定。
context: fork
agent: agents/detailed-design-doc.md
---

# 詳細設計書（DSD）作成スキル

## パラメータ

| パラメータ | 説明 | 例 |
|---|---|---|
| PROJECT_ID | プロジェクトID | PRJ-001 |
| PROJECT_NAME | プロジェクト名 | initial-build |
| FEAT_ID | 機能ID | FEAT-001 |
| FEAT_NAME | 機能名（英語・ケバブケース） | user-auth |

## エージェント起動

このスキルは以下のサブエージェントを使用して作業を実行する。1 回の起動で 1 つの FEAT-ID を担当する。複数 FEAT は別々のサブエージェントで並行して進められる。

| サブエージェント | タイプ | プロンプト |
|---|---|---|
| DSD 実行エージェント | general-purpose | `agents/detailed-design-doc.md` |

### 起動手順

1. `agents/detailed-design-doc.md` を Read で読み込む
2. `{{PROJECT_ID}}`, `{{PROJECT_NAME}}`, `{{FEAT_ID}}`, `{{FEAT_NAME}}` を実際の値に置換する
3. 以下の形式で Task ツールを呼び出してサブエージェントを起動する

> **重要**: このスキルの作業はすべてサブエージェントに委譲する。マスターエージェントが直接実行してはならない。

Task ツール呼び出し:
- `subagent_type`: `"general-purpose"`
- `description`: `"DSD 詳細設計 {FEAT_ID} 実行"`（例: `"DSD 詳細設計 FEAT-001 実行"`）
- `prompt`: 置換済みの agents/detailed-design-doc.md の内容全文
- `context`: `"fork"`

### 複数 FEAT の並行起動

複数 FEAT を処理する場合、FEAT ごとに独立した Task ツールを**同一メッセージ内で並行に**呼び出す。

例（FEAT-001 と FEAT-002 を並行実行）:
- Task 1: `subagent_type: "general-purpose"`, `description: "DSD 詳細設計 FEAT-001 実行"`, `prompt: （FEAT-001 用に置換した agents/detailed-design-doc.md）`, `context: "fork"`
- Task 2: `subagent_type: "general-purpose"`, `description: "DSD 詳細設計 FEAT-002 実行"`, `prompt: （FEAT-002 用に置換した agents/detailed-design-doc.md）`, `context: "fork"`

## ドキュメント対応表

| ドキュメントID | ドキュメント名 | 作成単位 | 入力元 | 保存先 |
|---|---|---|---|---|
| DSD-001_{FEAT-ID} | バックエンド機能詳細設計書 | 機能別 | BSD-001, BSD-002, BSD-004, BSD-009, DSD-009_{FEAT-ID}, REQ-005 | `docs/DSD/FEAT-{NNN}_{機能名}/DSD-001_{FEAT-ID}_{機能名}.md` |
| DSD-002_{FEAT-ID} | フロントエンド詳細設計書 | 機能別 | BSD-003, BSD-004, REQ-005 | `docs/DSD/FEAT-{NNN}_{機能名}/DSD-002_{FEAT-ID}_{機能名}.md` |
| DSD-003_{FEAT-ID} | API詳細設計書 | 機能別 | BSD-005, REQ-005 | `docs/DSD/FEAT-{NNN}_{機能名}/DSD-003_{FEAT-ID}_{機能名}.md` |
| DSD-004_{FEAT-ID} | データベース詳細設計書 | 機能別 | BSD-006, BSD-010, DSD-009_{FEAT-ID}, REQ-005 | `docs/DSD/FEAT-{NNN}_{機能名}/DSD-004_{FEAT-ID}_{機能名}.md` |
| DSD-005_{FEAT-ID} | 外部インターフェース詳細設計書 | 機能別（外部IF使用時のみ） | BSD-007, REQ-005 | `docs/DSD/FEAT-{NNN}_{機能名}/DSD-005_{FEAT-ID}_{機能名}.md` |
| DSD-006_{FEAT-ID} | バッチ・非同期処理詳細設計書 | 機能別（バッチ/非同期使用時のみ） | BSD-001, BSD-004, REQ-005 | `docs/DSD/FEAT-{NNN}_{機能名}/DSD-006_{FEAT-ID}_{機能名}.md` |
| DSD-007 | コーディング規約・開発ガイドライン | システム共通（1ファイルのみ） | BSD-001 | `docs/DSD/_common/DSD-007_coding-guidelines.md` |
| DSD-008_{FEAT-ID} | 単体テスト設計書 | 機能別 | DSD-001_{FEAT-ID}, DSD-002_{FEAT-ID}, DSD-003_{FEAT-ID}, DSD-009_{FEAT-ID} | `docs/DSD/FEAT-{NNN}_{機能名}/DSD-008_{FEAT-ID}_{機能名}.md` |
| DSD-009_{FEAT-ID} | ドメインモデル詳細設計書（DDD 戦術設計） | 機能別 | BSD-009, BSD-010, REQ-005 | `docs/DSD/FEAT-{NNN}_{機能名}/DSD-009_{FEAT-ID}_{機能名}.md` |

## 入力ドキュメントのパス

### BSDドキュメント（docs/BSD/）
| ドキュメントID | パス |
|---|---|
| BSD-001 | `docs/BSD/BSD-001_architecture.md` |
| BSD-002 | `docs/BSD/BSD-002_security-design.md` |
| BSD-003 | `docs/BSD/BSD-003_screen-design.md` |
| BSD-004 | `docs/BSD/BSD-004_business-flow.md` |
| BSD-005 | `docs/BSD/BSD-005_api-design.md` |
| BSD-006 | `docs/BSD/BSD-006_database-design.md` |
| BSD-007 | `docs/BSD/BSD-007_external-interface-design.md` |
| BSD-009 | `docs/BSD/BSD-009_domain-model.md` |
| BSD-010 | `docs/BSD/BSD-010_data-architecture.md` |

### REQドキュメント（docs/REQ/）
| ドキュメントID | パス |
|---|---|
| REQ-005 | `docs/REQ/REQ-005_feature-list.md` |

## 命名規則（重要）

- **機能名**: REQ-005 の機能名を英語・ケバブケース（kebab-case）に変換する（例: `user-auth`）
- **FEAT-ID**: REQ-005 で定義された `FEAT-{NNN}` をそのまま使用する
- **フォルダ名**: `FEAT-{NNN}_{機能名}` （例: `FEAT-001_user-auth`）
- **ファイル名**: `DSD-{NN}_FEAT-{NNN}_{機能名}.md` （例: `DSD-001_FEAT-001_user-auth.md`）
- DSD-007のみ例外: フォルダ `_common/`、ファイル名 `DSD-007_coding-guidelines.md`

## 作業ワークフロー

### Step 1: 対象の特定

ユーザーのリクエストから以下を特定する:
- **FEAT-ID**: どの機能（FEAT-NNN）か。未指定なら REQ-005 を読んで確認する
- **DSDドキュメント種別**: どの DSD（DSD-001〜DSD-009）か。「全部」の場合は以下の生成順序で処理

**生成順序**: `DSD-009 → DSD-001 → DSD-002 → DSD-003 → DSD-004 → DSD-005 → DSD-006 → DSD-007 → DSD-008`

> DSD-009 のドメインモデルが DSD-001（バックエンド）、DSD-004（DB）、DSD-008（テスト）の前提となるため、最初に生成する。

DSD-007（コーディング規約）はFEAT-IDを持たないシステム共通ドキュメント。

### Step 2: 入力ドキュメントの読み込み

対応表の「入力元」に記載されたドキュメントをすべて Read ツールで読み込む。ファイルが存在しない場合はユーザーに確認する。

**DSD-008 の場合は BSD ではなく同機能の DSD-001〜003 が入力元**（先に生成済みであることを確認する）。

### Step 3: テンプレートの読み込み

作成するドキュメントに対応するテンプレートを読み込む:

| 作成対象 | テンプレートファイル |
|---|---|
| DSD-001 | `references/dsd-001-backend.md` |
| DSD-002 | `references/dsd-002-frontend.md` |
| DSD-003 | `references/dsd-003-api.md` |
| DSD-004 | `references/dsd-004-database.md` |
| DSD-005 | `references/dsd-005-external-if.md` |
| DSD-006 | `references/dsd-006-batch.md` |
| DSD-007 | `references/dsd-007-coding-guidelines.md` |
| DSD-008 | `references/dsd-008-unit-test.md` |
| DSD-009 | `references/dsd-009-domain-model.md` |

### Step 4: ドキュメント生成

テンプレートのセクション構成に従い、入力ドキュメントの内容を基に具体的な内容を記載する。

**生成ルール:**
- 入力元に情報がない項目は `（要確認）` と記載し、空欄にしない
- ドキュメント冒頭に必ず **メタデータヘッダー** を記載する
- 用語は REQ-008（`docs/REQ/REQ-008_glossary.md`）が存在すれば参照して統一する

**メタデータヘッダー形式（機能別ドキュメント）:**
```markdown
# {ドキュメント名} - {機能名}

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-{NN}_{FEAT-ID} |
| 機能ID | {FEAT-NNN} |
| 機能名 | {機能名（日本語）} |
| バージョン | 1.0 |
| 作成日 | {今日の日付} |
| 入力元 | {BSD-XXX, REQ-005 など} |
| ステータス | 初版 |

---
```

**メタデータヘッダー形式（DSD-007 システム共通）:**
```markdown
# コーディング規約・開発ガイドライン

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-007 |
| バージョン | 1.0 |
| 作成日 | {今日の日付} |
| 入力元 | BSD-001 |
| ステータス | 初版 |

---
```

### Step 5: ファイル保存

1. 保存先フォルダが存在しない場合は `mkdir -p` で作成する
2. Write ツールで正しいパスに保存する
3. 保存後、ファイルパスとドキュメントIDをユーザーに報告する

---
name: implementation
description: |
  実装スキル。詳細設計書（DSD）を入力とし、単体テストスキル（skills/unit-test/）と連携して TDD の Red→Green→Refactor サイクルで実装を進め、実装完了報告書（IMP）を出力する。

  以下の場合に使用する：
  - 「実装して」「コードを書いて」などの依頼
  - 詳細設計書（DSD-001〜DSD-008）が揃っている機能の実装
  - バックエンド・フロントエンド・DB マイグレーションの実装
  - 実装完了後に IMP-001〜IMP-005 の報告書を作成する場合

  TDD サイクルの詳細（テストの書き方・テストダブル・FIRST 原則）は単体テストスキルを参照する。
  単体テストは実装と同時に完了する。UT フェーズは存在しない。

  入力: docs/DSD/ 以下の DSD-001〜DSD-008
  出力: projects/PRJ-{NNN}/IMP/ 以下の IMP-001〜IMP-005
  配置ルール・ドキュメント定義 → references/document-list.md
context: fork
agent: agents/implementation.md
---

# 実装スキル

## 概要

詳細設計書を読み込み、単体テストスキルの TDD サイクルに従って機能ごとに実装し、実装完了報告書を作成する。

参照ファイル：
- IMP ドキュメントテンプレート → `references/imp-templates.md`
- 配置ルール・ドキュメント定義 → `references/document-list.md`
- TDD サイクル詳細 → `skills/unit-test/references/tdd-workflow.md`（単体テストスキル側）

## パラメータ

| パラメータ | 説明 | 例 |
|---|---|---|
| PROJECT_ID | プロジェクトID | PRJ-001 |
| PROJECT_NAME | プロジェクト名 | initial-build |
| FEAT_ID | 機能ID | FEAT-001 |
| FEAT_NAME | 機能名（英語・ケバブケース） | user-auth |

## エージェント起動

このスキルは以下のサブエージェントを使用して作業を実行する。1 回の起動で 1 つの FEAT-ID を担当する。複数 FEAT は別々のサブエージェントで並行して進められる。

サブエージェントは本スキルと単体テストスキル（`skills/unit-test/SKILL.md`）の両方を読み込んで作業する。

| サブエージェント | タイプ | プロンプト |
|---|---|---|
| IMP 実行エージェント | general-purpose | `agents/implementation.md` |

### 起動手順

1. `agents/implementation.md` を Read で読み込む
2. `{{PROJECT_ID}}`, `{{PROJECT_NAME}}`, `{{FEAT_ID}}`, `{{FEAT_NAME}}` を実際の値に置換する
3. 以下の形式で Task ツールを呼び出してサブエージェントを起動する

> **重要**: このスキルの作業はすべてサブエージェントに委譲する。マスターエージェントが直接実行してはならない。

Task ツール呼び出し:
- `subagent_type`: `"general-purpose"`
- `description`: `"IMP 実装 {FEAT_ID} 実行"`（例: `"IMP 実装 FEAT-001 実行"`）
- `prompt`: 置換済みの agents/implementation.md の内容全文
- `context`: `"fork"`

### 複数 FEAT の並行起動

複数 FEAT を処理する場合、FEAT ごとに独立した Task ツールを**同一メッセージ内で並行に**呼び出す。

例（FEAT-001 と FEAT-002 を並行実行）:
- Task 1: `subagent_type: "general-purpose"`, `description: "IMP 実装 FEAT-001 実行"`, `prompt: （FEAT-001 用に置換した agents/implementation.md）`, `context: "fork"`
- Task 2: `subagent_type: "general-purpose"`, `description: "IMP 実装 FEAT-002 実行"`, `prompt: （FEAT-002 用に置換した agents/implementation.md）`, `context: "fork"`

## 並行作業スコープ

**このスキルは 1回の起動で 1つの FEAT-ID を担当する。**
複数の FEAT-ID は別セッションで並行して進める。

```
並行作業の例（FEAT-001 と FEAT-002 を同時に進める）:
  セッション A: FEAT-001 担当 → IMP-001_FEAT-001, IMP-002_FEAT-001 を作成
  セッション B: FEAT-002 担当 → IMP-001_FEAT-002, IMP-002_FEAT-002 を作成
  最後にまとめ: IMP-004 に両機能のマイグレーションを統合
```

**IMP-004（DB マイグレーション）は競合注意**:
- 各セッションは自分の FEAT-ID 分のマイグレーションを `IMP-004_FEAT-{NNN}_draft.md` として作成する
- 全 FEAT-ID の実装完了後、プロジェクト担当者が実行順序を調整して `IMP-004_db-migration.md` に統合する

## 前提確認

実装開始前に以下を確認する：

1. **対象 FEAT-ID の確認**: どの機能（FEAT-{NNN}）を実装するか
2. **プロジェクト ID の確認**: PRJ-{NNN} と出力先ディレクトリ
3. **実装範囲の確認**: バックエンドのみ / フロントエンドのみ / 両方
4. **FEAT 間依存の確認**: 依存する他の FEAT-ID が未実装でないか（DSD-001/002 の依存関係セクションを確認）
5. **初回構築かどうか**: IMP-003（環境構築手順書）が必要か

## 入力ドキュメントの読み込み方針

TDD では設計書を一括で読み込まない。**次のテストを書くのに必要な箇所だけ**その都度参照する。

```
最初に読む（スコープ把握のみ）
  docs/DSD/_common/DSD-007_coding-guidelines.md              ← コーディング規約（システム共通）
  docs/DSD/FEAT-{NNN}_{機能名}/DSD-008_{FEAT-ID}_{機能名}.md ← テストケース一覧を把握する

各イテレーションで必要に応じて参照する
  DSD-001 / DSD-002 ← 現在のテストケースが対象とするクラス/コンポーネントの仕様のみ読む
  DSD-003           ← 現在のテストケースが対象とする API エンドポイントの仕様のみ読む
  DSD-004           ← DB アクセスが必要になったときに読む
  DSD-005 / DSD-006 ← 外部IF・バッチが必要になったときに読む
```

> **アンチパターン**: 全 DSD を読んでから実装を始めない。読みすぎると設計を先取りしてしまい TDD の効果が失われる。

## TDD マイクロサイクル

**TDD サイクルの詳細は単体テストスキル（`skills/unit-test/SKILL.md`）に従う。**

テストリスト管理・Red→Green→Refactor の各ステップ・実装戦略（仮実装/三角測量/明白な実装）・テストダブル・FIRST 原則・アンチパターンについては、単体テストスキルおよび `skills/unit-test/references/tdd-workflow.md` を参照する。

実装スキルでは、Green フェーズでの実装コード作成と Refactor フェーズでのコード整理を担当する。

## DB マイグレーション

DSD-004 を元に、マイグレーションスクリプトを作成する。

**並行作業時の手順**:
1. 各 FEAT セッションは自分の担当分を `IMP-004_FEAT-{NNN}_draft.md` として作成する（`references/imp-templates.md` の IMP-004 テンプレートを使用）
2. 全 FEAT-ID の実装完了後、実行順序（テーブル依存関係）を調整して `IMP-004_db-migration.md` に統合する
3. 統合時に FEAT 間のテーブル依存（外部キー参照など）を考慮した実行順序を確定する

## 出力ドキュメントの作成

`references/imp-templates.md` のテンプレートを使い、機能ごとに以下を作成する：

| ドキュメント | 作成タイミング | 配置先 | 並行作業 |
|---|---|---|---|
| IMP-001_{FEAT-ID}_{機能名}.md | BE TDD サイクル完了後 | `projects/PRJ-{NNN}/IMP/FEAT-{NNN}_{機能名}/` | 各 FEAT 独立 |
| IMP-002_{FEAT-ID}_{機能名}.md | FE TDD サイクル完了後 | `projects/PRJ-{NNN}/IMP/FEAT-{NNN}_{機能名}/` | 各 FEAT 独立 |
| IMP-003_environment-setup.md | 初回構築時のみ（1セッションで作成） | `projects/PRJ-{NNN}/IMP/` | 単独作成 |
| IMP-004_FEAT-{NNN}_draft.md | DB 変更がある FEAT の TDD 完了後 | `projects/PRJ-{NNN}/IMP/` | 各 FEAT 独立で下書き作成 |
| IMP-004_db-migration.md | 全 FEAT 完了後に統合 | `projects/PRJ-{NNN}/IMP/` | draft をマージして完成 |
| IMP-005_tdd-defect-list.md | TDD 中に不具合が発生した都度更新 | `projects/PRJ-{NNN}/IMP/` | 全 FEAT 共通（随時追記） |

## 設計差異の記録原則

実装中に DSD との差異が生じた場合：
1. 差異内容・理由を記録する（IMP-001/002 の「設計差異一覧」に記載）
2. 差異が設計変更を要する場合はユーザーに確認し、必要なら DSD を更新する
3. 既知の制限事項（将来対応）は「既知の制限事項」セクションに記載する

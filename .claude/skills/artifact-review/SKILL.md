---
name: artifact-review
description: |
  成果物レビュースキル。ウォーターフォール開発の各フェーズ完了時に、前後フェーズ間の成果物の
  整合性・FEAT-IDトレーサビリティを検証し、次フェーズへの移行可否を判定するレビュー報告書
  （REV-001〜REV-004）を出力する。

  以下の場合に使用する：
  - 「レビューして」「フェーズレビューを実施して」「REV-001を作成して」などの依頼
  - 各フェーズ完了後の次フェーズ移行可否の判断
  - FEAT-IDトレーサビリティ確認（要件定義 → 設計 → 実装 → テストの一貫性）
  - フェーズ間の成果物不整合・漏れの発見

  レビュー種別と出力：
  - REV-001: REQ → BSD レビュー（BSD完了時）
  - REV-002: BSD → DSD レビュー（DSD完了時）
  - REV-003: DSD → IMP レビュー（IMP完了時）
  - REV-004: IMP → IT/ST レビュー（IT/ST完了時）

  入力: 各フェーズの成果物（REQ/BSD/DSD/IMP/IT/ST ドキュメント）
  出力: projects/PRJ-{NNN}/REV/ 以下の REV-001〜REV-004
  配置ルール・ドキュメント定義 → references/document-list.md
context: fork
agents:
  - name: artifact-review
    file: agents/artifact-review.md
    subagent_type: general-purpose
    role: レビューオーケストレーター（メイン起動）
  - name: artifact-explorer
    file: agents/artifact-explorer.md
    subagent_type: Explore
    role: 成果物ファイル探索
---

# 成果物レビュースキル（artifact-review）

## 概要

フェーズ整合性監査専門家として、ウォーターフォール開発の各フェーズ間の成果物整合性を検証する。オーケストレーターが探索サブエージェントを統括し、FEAT-ID トレーサビリティの確認・問題の重大度分類・次フェーズ移行判定・レビュー報告書作成を担当する。

参照ファイル:
- レビュー基準チェックリスト → `references/review-criteria.md`
- REV ドキュメントテンプレート → `references/rev-templates.md`
- 配置ルール・ドキュメント定義 → `references/document-list.md`

## パラメータ

| パラメータ | 説明 | 例 |
|---|---|---|
| PROJECT_ID | プロジェクトID（PRJ-NNN形式） | PRJ-001 |
| PROJECT_NAME | プロジェクト名（kebab-case） | initial-build |
| REVIEW_TYPE | レビュー種別 | REQ-BSD / BSD-DSD / DSD-IMP / IMP-TEST |

### REVIEW_TYPE の有効値

| REVIEW_TYPE | 説明 | 出力ドキュメント | 実行タイミング |
|---|---|---|---|
| `REQ-BSD` | REQ フェーズ → BSD フェーズのレビュー | REV-001_req-to-bsd.md | BSD 完了時 |
| `BSD-DSD` | BSD フェーズ → DSD フェーズのレビュー | REV-002_bsd-to-dsd.md | DSD 完了時 |
| `DSD-IMP` | DSD フェーズ → IMP フェーズのレビュー | REV-003_dsd-to-imp.md | IMP 完了時 |
| `IMP-TEST` | IMP フェーズ → IT/ST フェーズのレビュー | REV-004_imp-to-test.md | IT/ST 完了時 |

## エージェント起動

このスキルは以下のオーケストレーターエージェントを使用して作業を実行する。オーケストレーターは内部で成果物探索サブエージェントを起動する。

| サブエージェント | タイプ | プロンプト |
|---|---|---|
| レビューオーケストレーター | general-purpose | `agents/artifact-review.md` |

### 起動手順

1. `agents/artifact-review.md` を Read で読み込む
2. `{{PROJECT_ID}}`, `{{PROJECT_NAME}}`, `{{REVIEW_TYPE}}` を実際の値に置換する
3. 以下の形式で Task ツールを呼び出してサブエージェントを起動する

> **重要**: このスキルの作業はすべてサブエージェントに委譲する。マスターエージェントが直接実行してはならない。

Task ツール呼び出し:
- `subagent_type`: `"general-purpose"`
- `description`: `"フェーズ間成果物レビュー {{REVIEW_TYPE}} {{PROJECT_ID}}"`
- `prompt`: 置換済みの agents/artifact-review.md の内容全文
- `context`: `"fork"`

## サブエージェント構成

```
レビューオーケストレーター（agents/artifact-review.md / general-purpose）
  │
  ├── Phase A: スキル定義・基準読込・FEAT-ID一覧取得（オーケストレーター自身）
  │     docs/REQ/REQ-005_feature-list.md から FEAT-IDリストを構築
  │
  ├── Phase B: 成果物探索（Explore サブエージェント × 1回）
  │     agents/artifact-explorer.md を使用
  │     → 上流・下流全ファイルのパス・存在有無を返却
  │
  ├── Phase C: 成果物読込・整合性検証（オーケストレーター自身）
  │     review-criteria.md の基準に従いフェーズ固有チェックを実施
  │     FEAT-ID トレーサビリティマトリクスを構築
  │     問題点を Critical/Major/Minor で分類
  │
  └── Phase D: レビュー報告書作成（オーケストレーター自身）
        rev-templates.md テンプレートに従い REV-NNN を生成・保存
        次フェーズ移行判定: PASS / CONDITIONAL PASS / FAIL
```

| Phase | 担当 | サブエージェントタイプ |
|---|---|---|
| A | オーケストレーター自身 | - |
| B | 成果物探索 | Explore |
| C | オーケストレーター自身 | - |
| D | オーケストレーター自身 | - |

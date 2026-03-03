---
name: acceptance-test
description: |
  受入テスト（UAT）スキル。エンドユーザー・業務担当者のペルソナになりきり、
  サブエージェントを活用して FEAT 単位で並行にソースコード検証・ブラウザテストを実施する。
  ST-001（システムテスト）と要件定義書を入力とし、ユーザー視点で業務要件の充足を確認し、
  受入テスト仕様・結果書（UAT-001）・不具合管理票（UAT-002）・受入完了報告書（UAT-003）を出力する。

  以下の場合に使用する：
  - 「受入テストして」「UATフェーズを実施して」「UAT-001を作成して」などの依頼
  - ST-001（システムテスト仕様・結果書）が PASS しているプロジェクトの受入テスト
  - ユーザー・発注者視点での業務要件充足確認
  - 受入完了後のリリース可否判断（UAT-003作成）

  入力: REQ-001, REQ-002, REQ-003, REQ-005, ST-001, ST-004、実装済みソースコード
  出力: projects/PRJ-{NNN}/UAT/ 以下の UAT-001〜UAT-003
  配置ルール・ドキュメント定義 → references/document-list.md
context: fork
agents:
  - name: acceptance-test
    file: agents/acceptance-test.md
    subagent_type: general-purpose
    role: UAT オーケストレーター（メイン起動）
  - name: uat-code-explorer
    file: agents/uat-code-explorer.md
    subagent_type: Explore
    role: Phase B コード探索（FEAT 並行）
  - name: uat-scenario-runner
    file: agents/uat-scenario-runner.md
    subagent_type: general-purpose
    role: Phase C シナリオテスト実行（FEAT 並行）
  - name: uat-browser-runner
    file: agents/uat-browser-runner.md
    subagent_type: general-purpose
    role: Phase D ブラウザテスト実行（未実装）
---

# 受入テストスキル（UAT）

## 概要

エンドユーザーになりきり、サブエージェントを活用して FEAT 単位で並行にテストを実施する。オーケストレーターがペルソナ構築・シナリオ設計・結果集約を担当し、個別の検証作業はサブエージェントに委譲する。

参照ファイル：
- UAT ドキュメントテンプレート → `references/uat-templates.md`
- 配置ルール・ドキュメント定義 → `references/document-list.md`

## パラメータ

| パラメータ | 説明 | 例 |
|---|---|---|
| PROJECT_ID | プロジェクトID | PRJ-001 |
| PROJECT_NAME | プロジェクト名 | initial-build |

## エージェント起動

このスキルは以下のオーケストレーターエージェントを使用して作業を実行する。オーケストレーターは内部でさらにサブエージェント（コード探索・シナリオテスト実行）を起動する。

| サブエージェント | タイプ | プロンプト |
|---|---|---|
| UAT オーケストレーター | general-purpose | `agents/acceptance-test.md` |

### 起動手順

1. `agents/acceptance-test.md` を Read で読み込む
2. `{{PROJECT_ID}}`, `{{PROJECT_NAME}}` を実際の値に置換する
3. 以下の形式で Task ツールを呼び出してサブエージェントを起動する

> **重要**: このスキルの作業はすべてサブエージェントに委譲する。マスターエージェントが直接実行してはならない。

Task ツール呼び出し:
- `subagent_type`: `"general-purpose"`
- `description`: `"UAT 受入テスト実行"`
- `prompt`: 置換済みの agents/acceptance-test.md の内容全文
- `context`: `"fork"`

## サブエージェント構成

```
UAT オーケストレーター（本エージェント）
  │
  ├── Phase A: 入力読込・ペルソナ構築・シナリオ設計（オーケストレーター自身）
  │
  ├── Phase B: コード探索（Explore サブエージェント × FEAT 数、並行）
  │     agents/uat-code-explorer.md を使用
  │     → 各 FEAT の FE/BE ソースコードファイルパスを特定
  │
  ├── Phase C: シナリオテスト実行（general-purpose サブエージェント × FEAT 数、並行）
  │     agents/uat-scenario-runner.md を使用
  │     → 各 FEAT のソースコードを追跡し UTC テストケースを検証
  │
  ├── Phase D: ブラウザテスト実行（将来実装）
  │     agents/uat-browser-runner.md を使用
  │     → Playwright で実際のブラウザ操作を検証
  │
  └── Phase E: 結果集約・ドキュメント作成（オーケストレーター自身）
        → UAT-001, UAT-002, UAT-003 を生成
```

| Phase | 担当 | サブエージェントタイプ | 並行 |
|---|---|---|---|
| A | オーケストレーター自身 | - | - |
| B | コード探索 | Explore | FEAT 並行 |
| C | シナリオテスト実行 | general-purpose | FEAT 並行 |
| D | ブラウザテスト実行（未実装） | general-purpose | FEAT 並行 |
| E | オーケストレーター自身 | - | - |

## ユーザーペルソナの採用（Phase A: オーケストレーターが実施）

受入テストでは**技術者の視点を捨て、エンドユーザー（業務担当者・発注者）になりきる**。

### ペルソナ構築手順

1. REQ-002（業務要件）から業務担当者の役割・日常業務を把握する
2. REQ-003（ユースケース）のアクター定義からペルソナ像を特定する
3. 以下の観点でペルソナを設定する：

| 設定項目 | 内容 |
|---|---|
| 役割 | REQ-003 のアクター（例: 店舗スタッフ、管理者、一般会員） |
| ITリテラシー | 業務担当者レベル（技術用語は使わない） |
| 関心事 | 業務が滞りなく回るか・操作が直感的か・エラー時に困らないか |
| 評価基準 | 要件どおりに動くか（実装の内部品質ではなく業務上の正しさ） |

構築したペルソナ定義テキストは、シナリオテスト実行サブエージェントに渡す。

### テスト中の思考（サブエージェントにも共有する）

- 「この画面を初めて見たユーザーは迷わず操作できるか？」
- 「業務ルールどおりに動いているか？」（REQ-002 の業務ルールと照合）
- 「エラーが起きたとき、ユーザーは何をすればいいか分かるか？」
- 「一連の業務フロー（登録→確認→変更→削除）を通しで実行できるか？」

## 受入シナリオ設計（Phase A: オーケストレーターが実施）

REQ-002（業務要件）・REQ-003（ユースケース）・REQ-005（機能一覧）を元に、テストケースを設計する。

### シナリオ設計の手順

1. REQ-005 から対象 FEAT-ID 一覧を取得する
2. 各ユースケースに対応する業務シナリオテストを設計する
3. REQ-002 の各業務ルールに対応する確認テストを設計する
4. ST-004 の保留不具合に対応する再確認テストを設計する
5. **各 UTC を FEAT-ID に割り当てる**

テストケース ID は `UTC-{NNN}` 形式（プロジェクト内で連番）で採番する。

**シナリオ設計の原則**：
- **業務言語で記述する**: 技術用語は使わず、ユーザーの操作と期待する結果を業務言語で書く
- **ユースケースの主シナリオ・代替シナリオを網羅する**
- **業務上クリティカルな操作を優先する**: 金銭・権限・データ削除に関わる操作は必ずテストする

## コード探索（Phase B: Explore サブエージェント）

`agents/uat-code-explorer.md` を Read で読み込み、FEAT ごとに Explore サブエージェントを起動する。

Task ツール呼び出し（FEAT ごとに並行）:
- `subagent_type`: `"Explore"`
- `description`: `"UAT コード探索 {FEAT_ID}"`（例: `"UAT コード探索 FEAT-001"`）
- `prompt`: 置換済みの agents/uat-code-explorer.md の内容全文（`{{FEAT_ID}}`, `{{FEAT_NAME}}` を置換）
- `context`: `"fork"`

```
複数 FEAT を並行で起動してよい。
各サブエージェントは以下を返す:
  - FE ファイルパス一覧（ページ・コンポーネント・API クライアント・ルーティング）
  - BE ファイルパス一覧（コントローラー・サービス・リポジトリ・ドメインモデル・バリデーション）
```

## シナリオテスト実行（Phase C: general-purpose サブエージェント）

`agents/uat-scenario-runner.md` を Read で読み込み、FEAT ごとに general-purpose サブエージェントを起動する。

Task ツール呼び出し（FEAT ごとに並行）:
- `subagent_type`: `"general-purpose"`
- `description`: `"UAT シナリオテスト {FEAT_ID}"`（例: `"UAT シナリオテスト FEAT-001"`）
- `prompt`: 置換済みの agents/uat-scenario-runner.md の内容全文（`{{FEAT_ID}}`, `{{FEAT_NAME}}`, `{{PERSONA}}`, `{{UTC_LIST}}`, `{{SOURCE_FILES}}`, `{{BUG_ID_START}}` を置換）
- `context`: `"fork"`

### サブエージェントに渡す情報

| 項目 | 内容 |
|---|---|
| FEAT_ID / FEAT_NAME | 対象機能 |
| PERSONA | Phase A で構築したペルソナ定義テキスト |
| UTC_LIST | Phase A で当該 FEAT に割り当てた UTC テストケース一覧 |
| SOURCE_FILES | Phase B で取得した FE/BE ファイルパス一覧 |
| BUG_ID_START | ST-004 最終 BUG-ID + 1 から FEAT ごとに 50 ずつ割り当てた開始番号 |

### BUG-ID 衝突防止

ST-004 の最終 BUG-ID を確認し、FEAT ごとに 50 件分の BUG-ID 範囲を事前割り当てする。

```
例: ST-004 の最終 BUG-ID が BUG-010 の場合
  FEAT-001: BUG-011 〜 BUG-060
  FEAT-002: BUG-061 〜 BUG-110
  FEAT-003: BUG-111 〜 BUG-160
```

### サブエージェントの検証方法

各サブエージェントはソースコードを読み解き、ユーザー操作をシミュレーションする：

| 優先度 | 検証観点 | 確認方法 |
|---|---|---|
| 1 | 主要業務フローが正常に完了するか | FE 画面遷移 + API + BE ロジックを通しで追跡 |
| 2 | 業務ルールが正しく実装されているか | REQ-002 の各ルールと BE バリデーション/ロジックを照合 |
| 3 | エラー時にユーザーが困らないか | FE のエラーハンドリング・メッセージ表示を確認 |
| 4 | 画面の文言が業務担当者に分かりやすいか | FE コンポーネントのラベル・UIテキストを確認 |
| 5 | ST 保留不具合が解消されているか | ST-004 の該当コード箇所を再確認 |

## 結果集約とドキュメント作成（Phase E: オーケストレーターが実施）

### 集約手順

1. 全サブエージェントの返却結果を収集する
2. 全 FEAT の UTC 結果を統合する
3. 全 FEAT の不具合（BUG-ID）を統合し、実際に使用された番号だけに再採番する
4. テスト結果サマリー（OK / NG / SKIP 件数）を算出する

### 完了判定

| 判定基準 | 内容 |
|---|---|
| PASS 条件 | 全 UTC が OK または SKIP（SKIP は理由必記）。重大度「高」の不具合が残存しないこと |
| FAIL 条件 | NG が残存（特に業務上クリティカルな項目は修正必須） |
| 品質基準 | BSD-008 の UAT 合格基準を参照 |

### 不具合の重大度定義

| 重大度 | 定義 | 対応方針 |
|---|---|---|
| 高 | 業務が成立しない / 受入基準を満たさないクリティカルな不具合 | **即時報告** + 修正・再テスト必須 |
| 中 | 業務要件と動作が異なる / 一部シナリオが失敗するが回避策あり | 修正後に再テスト |
| 低 | 軽微な表示差異・文言の誤り・UX 上の改善点 | リリース判定で合否を決定 |

### 出力ドキュメント

`references/uat-templates.md` のテンプレートを使い、以下を作成する：

| ドキュメント | 作成タイミング | 配置先 |
|---|---|---|
| UAT-001_acceptance-test.md | 全サブエージェント完了後 | `projects/PRJ-{NNN}/UAT/` |
| UAT-002_defect-list.md | 不具合集約後 | `projects/PRJ-{NNN}/UAT/` |
| UAT-003_acceptance-report.md | UAT-001・UAT-002 完了後 | `projects/PRJ-{NNN}/UAT/` |

> BUG-ID は ST-004 の採番から継続して通番。集約後に歯抜けを詰めて再採番する。

## リリースフェーズへの申し送り原則

1. **リリース可否の明示**: UAT-003 にリリース可否判断を明記する
2. **保留不具合の引き継ぎ**: UAT-002 の保留不具合をリリース後の対応方針とともに記載する
3. **受入条件付き PASS の場合**: 条件（修正必須項目・確認事項）を明記する
4. **本番環境固有の確認事項**: テスト環境と本番環境の差異を申し送る

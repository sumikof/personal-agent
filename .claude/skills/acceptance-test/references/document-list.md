# ウォーターフォール開発 ドキュメント一覧（UAT 関連セクション）

> このファイルは `document-list.md` の UAT 関連セクションの参照コピーです。
> 配置ルール・ドキュメント定義の確認用。

---

## ドキュメントID 体系

| プレフィックス | フェーズ | 例 |
|---|---|---|
| `REQ` | 要件定義 | REQ-001 |
| `BSD` | 基本設計 | BSD-001 |
| `DSD` | 詳細設計 | DSD-001 |
| `IMP` | 実装・単体テスト（TDD） | IMP-001 |
| `IT` | 結合テスト | IT-001 |
| `ST` | システムテスト | ST-001 |
| `UAT` | 受入テスト | UAT-001 |
| `REL` | リリース | REL-001 |
| `OPS` | 運用・保守 | OPS-001 |
| `FEAT` | 機能識別子（REQ-005で定義） | FEAT-001 |
| `PRJ` | プロジェクト識別子 | PRJ-001 |

---

## フェーズ7: 受入テスト (UAT)

> **配置先**: すべて `projects/PRJ-{NNN}/UAT/`（プロジェクト固有）。

### ドキュメント一覧

| ドキュメントID | ドキュメント名 | ファイル名 | 説明 | 入力元(トレース) | 後続フェーズへの影響 |
|---|---|---|---|---|---|
| UAT-001 | 受入テスト仕様・結果書 | `UAT-001_acceptance-test.md` | ユーザー視点のシナリオテスト・業務要件充足確認 | REQ-001, REQ-002, REQ-003, ST-001 | REL-001 |
| UAT-002 | 不具合管理票（受入テスト） | `UAT-002_defect-list.md` | バグID・発生箇所・重大度・対応状況・修正結果 | UAT-001 | REL-001 |
| UAT-003 | 受入完了報告書 | `UAT-003_acceptance-report.md` | テスト合否判定・残課題・リリース可否判断 | UAT-001, UAT-002 | REL-001 |

### 成果物チェックリスト

- [ ] UAT-001 受入テスト仕様・結果書
- [ ] UAT-002 不具合管理票（受入テスト）
- [ ] UAT-003 受入完了報告書

---

## ディレクトリツリー（UAT フォルダ部分）

```
projects/
└── PRJ-{NNN}_{プロジェクト名}/
    └── UAT/
        ├── UAT-001_acceptance-test.md    # 受入テスト仕様・結果書
        ├── UAT-002_defect-list.md        # 不具合管理票（テスト中随時更新）
        └── UAT-003_acceptance-report.md  # 受入完了報告書（UAT完了後に作成）
```

### フォルダ・ファイル命名規則

| フォルダ・ファイル | 命名形式 | 例 |
|---|---|---|
| プロジェクトフォルダ | `PRJ-{NNN}_{プロジェクト名}/` | `PRJ-001_initial-build/` |
| UAT-001（受入テスト） | `UAT-001_acceptance-test.md` | `UAT-001_acceptance-test.md` |
| UAT-002（不具合管理票） | `UAT-002_defect-list.md` | `UAT-002_defect-list.md` |
| UAT-003（受入完了報告書） | `UAT-003_acceptance-report.md` | `UAT-003_acceptance-report.md` |

---

## 工程間トレース（UAT フェーズの入出力）

```
# 受入テスト（UAT）の入出力

入力:
  projects/PRJ-{NNN}/BSD/BSD-008_test-plan.md              ← テスト計画・UAT合格基準・受入条件
  projects/PRJ-{NNN}/REQ/REQ-001_system-requirements.md   ← システム要件（受入基準）
  projects/PRJ-{NNN}/REQ/REQ-002_business-requirements.md ← 業務要件・業務ルール
  projects/PRJ-{NNN}/REQ/REQ-003_use-cases.md             ← ユースケース（シナリオ設計元）
  projects/PRJ-{NNN}/ST/ST-001_system-test.md             ← システムテスト結果・UAT申し送り
  projects/PRJ-{NNN}/ST/ST-004_defect-list.md             ← ST保留不具合（UAT-001での再確認対象）

出力:
  UAT-001_acceptance-test.md    ← 受入テスト仕様・結果書（ユーザーシナリオテスト）
  UAT-002_defect-list.md        ← 不具合管理票（テスト中随時更新）
  UAT-003_acceptance-report.md  ← 受入完了報告書（リリース可否判断・関係者承認）

後続:
  REL-001_release-plan.md       ← リリース計画書への入力
```

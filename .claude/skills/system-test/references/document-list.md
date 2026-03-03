# ウォーターフォール開発 ドキュメント一覧（ST 関連セクション）

> このファイルは `document-list.md` の ST 関連セクションの参照コピーです。
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

## フェーズ6: システムテスト (ST)

> **配置先**: すべて `projects/PRJ-{NNN}/ST/`（プロジェクト固有）。

### ドキュメント一覧

| ドキュメントID | ドキュメント名 | ファイル名 | 説明 | 入力元(トレース) | 後続フェーズへの影響 |
|---|---|---|---|---|---|
| ST-001 | システムテスト仕様・結果書 | `ST-001_system-test.md` | シナリオベースのE2Eテストケース・業務フロー全体の検証結果 | BSD-008, REQ-003, REQ-005, IT-001_{FEAT-ID} | UAT-001 |
| ST-002 | 性能テスト仕様・結果書 | `ST-002_performance-test.md` | 負荷試験・レスポンスタイム計測・スループット確認 | REQ-006, ST-001 | UAT-001 |
| ST-003 | セキュリティテスト仕様・結果書 | `ST-003_security-test.md` | 脆弱性診断・認証/認可テスト・通信暗号化確認 | REQ-006, BSD-002, ST-001 | UAT-001 |
| ST-004 | 不具合管理票（システムテスト） | `ST-004_defect-list.md` | バグID・発生箇所・重大度・対応状況・修正結果 | ST-001, ST-002, ST-003 | UAT-001 |

### 成果物チェックリスト

- [ ] ST-001 システムテスト仕様・結果書
- [ ] ST-002 性能テスト仕様・結果書
- [ ] ST-003 セキュリティテスト仕様・結果書
- [ ] ST-004 不具合管理票（システムテスト）

---

## ディレクトリツリー（ST フォルダ部分）

```
projects/
└── PRJ-{NNN}_{プロジェクト名}/
    └── ST/
        ├── ST-001_system-test.md         # システムテスト仕様・結果書
        ├── ST-002_performance-test.md    # 性能テスト仕様・結果書
        ├── ST-003_security-test.md       # セキュリティテスト仕様・結果書
        └── ST-004_defect-list.md         # 不具合管理票（テスト中随時更新）
```

### フォルダ・ファイル命名規則

| フォルダ・ファイル | 命名形式 | 例 |
|---|---|---|
| プロジェクトフォルダ | `PRJ-{NNN}_{プロジェクト名}/` | `PRJ-001_initial-build/` |
| ST-001（システムテスト） | `ST-001_system-test.md` | `ST-001_system-test.md` |
| ST-002（性能テスト） | `ST-002_performance-test.md` | `ST-002_performance-test.md` |
| ST-003（セキュリティテスト） | `ST-003_security-test.md` | `ST-003_security-test.md` |
| ST-004（不具合管理票） | `ST-004_defect-list.md` | `ST-004_defect-list.md` |

---

## 工程間トレース（ST フェーズの入出力）

```
# システムテスト（ST）の入出力

入力:
  BSD-008_test-plan.md                      ← テスト計画・品質基準・ST合格基準
  REQ-003_use-cases.md                      ← ユースケース（E2Eシナリオの設計元）
  REQ-005_feature-list.md                   ← 機能一覧（テスト対象機能の確認）
  REQ-006_non-functional-requirements.md    ← 性能・セキュリティ要件（ST-002・ST-003の基準）
  BSD-002_security-design.md                ← セキュリティ基本設計（ST-003の入力）
  IT-001_{FEAT-ID}_{機能名}.md              ← 結合テスト結果・申し送り（全FEAT-ID分）
  IT-002_api-integration-test.md            ← API結合テスト結果
  IT-003_defect-list.md                     ← IT保留不具合（ST-001での再確認対象）

出力:
  ST-001_system-test.md                     ← システムテスト仕様・結果書（E2E・業務フロー）
  ST-002_performance-test.md                ← 性能テスト仕様・結果書（負荷試験）
  ST-003_security-test.md                   ← セキュリティテスト仕様・結果書（脆弱性診断）
  ST-004_defect-list.md                     ← 不具合管理票（テスト中随時更新）

後続:
  UAT-001_acceptance-test.md                ← 受入テストへの入力
```

# ウォーターフォール開発 ドキュメント一覧（IT 関連セクション）

> このファイルは `document-list.md` の IT 関連セクションの参照コピーです。
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

## フェーズ5: 結合テスト (IT)

> **配置先**: すべて `projects/PRJ-{NNN}/IT/`（プロジェクト固有）。
>
> **作成単位**: IT-001は機能別（機能単位の結合シナリオ）、IT-002・IT-003はプロジェクト共通。

### ドキュメント一覧

| ドキュメントID | ドキュメント名 | ファイル名 | 作成単位 | 説明 | 入力元(トレース) | 後続フェーズへの影響 |
|---|---|---|---|---|---|---|
| IT-001_{FEAT-ID} | 結合テスト仕様・結果書 | `IT-001_{FEAT-ID}_{機能名}.md` | 機能別 | 機能単位のフロントエンド/バックエンド間・外部システム連携の結合テストケースと結果 | BSD-008, DSD-003_{FEAT-ID}, DSD-005_{FEAT-ID}, IMP-001_{FEAT-ID}, IMP-002_{FEAT-ID} | ST-001 |
| IT-002 | API結合テスト仕様・結果書 | `IT-002_api-integration-test.md` | システム共通 | 全APIエンドポイントの実動作確認・レスポンス検証（全機能横断） | DSD-003_{FEAT-ID}, IT-001_{FEAT-ID} | ST-001 |
| IT-003 | 不具合管理票（結合テスト） | `IT-003_defect-list.md` | システム共通 | バグID・発生箇所（FEAT-ID付）・重大度・対応状況・修正結果（全機能を集約） | IT-001_{FEAT-ID}, IT-002 | ST-001 |

### 成果物チェックリスト

- [ ] IT-001_{FEAT-ID} 結合テスト仕様・結果書（機能ごとに作成）
- [ ] IT-002 API結合テスト仕様・結果書
- [ ] IT-003 不具合管理票（結合テスト）

---

## ディレクトリツリー（IT フォルダ部分）

```
projects/
└── PRJ-{NNN}_{プロジェクト名}/
    └── IT/
        ├── IT-002_api-integration-test.md    # 全IT-001完了後に作成
        ├── IT-003_defect-list.md             # テスト中随時更新
        ├── FEAT-001_{機能名}/
        │   └── IT-001_FEAT-001_{機能名}.md  # 機能別・並行作業可
        └── FEAT-NNN_{機能名}/
            └── IT-001_FEAT-NNN_{機能名}.md
```

### フォルダ・ファイル命名規則

| フォルダ・ファイル | 命名形式 | 例 |
|---|---|---|
| プロジェクトフォルダ | `PRJ-{NNN}_{プロジェクト名}/` | `PRJ-001_initial-build/` |
| 機能別サブフォルダ | `FEAT-{NNN}_{機能名}/` | `FEAT-001_user-auth/` |
| IT-001（機能別） | `IT-001_{FEAT-ID}_{機能名}.md` | `IT-001_FEAT-001_user-auth.md` |
| IT-002（システム共通） | `IT-002_api-integration-test.md` | `IT-002_api-integration-test.md` |
| IT-003（システム共通） | `IT-003_defect-list.md` | `IT-003_defect-list.md` |

---

## 工程間トレース（IT フェーズの入出力）

```
# FEAT-001（例: ユーザー認証）の IT ドキュメント群

入力:
  BSD-008_test-plan.md               ← テスト計画・品質基準
  DSD-003_FEAT-001_user-auth.md      ← API詳細仕様
  DSD-005_FEAT-001_user-auth.md      ← 外部IF仕様（該当時のみ）
  IMP-001_FEAT-001_user-auth.md      ← BE実装・申し送り
  IMP-002_FEAT-001_user-auth.md      ← FE実装・申し送り

出力:
  IT-001_FEAT-001_user-auth.md       ← 結合テスト仕様・結果書（機能別）
  IT-002_api-integration-test.md     ← API結合テスト（全FEAT-ID完了後）
  IT-003_defect-list.md              ← 不具合管理票（随時更新）

後続:
  ST-001_system-test.md              ← システムテストへの入力
```

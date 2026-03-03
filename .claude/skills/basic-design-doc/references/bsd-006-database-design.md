# BSD-006 データベース基本設計書 テンプレート

## セクション構成

```markdown
## 1. データベース設計方針

### 1.1 使用DBMS
（REQ-001 または BSD-001 から）
- DBMS: （例: PostgreSQL 15）
- 文字コード: UTF-8
- タイムゾーン: Asia/Tokyo

### 1.2 設計方針
- 正規化レベル: 第3正規形を基本とする
- 論理削除: 採用 / 非採用 （採用の場合: `deleted_at` カラム）
- 監査カラム: `created_at`, `updated_at`, `created_by`, `updated_by`
- ID方針: UUID / 連番 / ULID など

### 1.3 DDD 整合データモデリング方針
- テーブルは集約単位でグループ化する。1つの集約は1つのトランザクション境界に対応する
- 境界づけられたコンテキストごとにスキーマ所有権を定義する（スキーマ分離 or テーブルプレフィックス）
- 値オブジェクトの永続化戦略: 埋め込み（同一テーブルのカラム） vs 分離テーブル
  - 単純な値オブジェクト（Email, Money 等）: 埋め込みを基本とする
  - 複合値オブジェクト（Address 等）: 分離テーブルも検討する

> 詳細は BSD-009（ドメインモデル設計書）、BSD-010（データアーキテクチャ設計書）を参照。

---

## 2. ER図（概念レベル）

（Mermaid の erDiagram でエンティティと関係を図示）

```mermaid
erDiagram
  USERS {
    uuid id PK
    string email
    string name
    timestamp created_at
  }
  ORDERS {
    uuid id PK
    uuid user_id FK
    timestamp ordered_at
  }
  USERS ||--o{ ORDERS : "places"
```

---

## 3. テーブル一覧

（REQ-005 の機能一覧・REQ-007 の外部IFから）

| テーブル名 | 論理名 | 概要 | 境界づけられたコンテキスト | 集約 | 関連FEAT-ID |
|---|---|---|---|---|---|
| `users` | ユーザー | システム利用者情報 | CTX-XXX | User集約 | FEAT-XXX |
| `orders` | 注文 | 注文情報 | CTX-YYY | Order集約 | FEAT-XXX |

---

## 4. テーブル定義（主要テーブル）

### 4.1 `{テーブル名}`（{論理名}）

**概要**: {テーブルの役割}

| カラム名 | 型 | 制約 | 説明 |
|---|---|---|---|
| `id` | UUID | PK, NOT NULL | 主キー |
| `name` | VARCHAR(255) | NOT NULL | 名称 |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | 作成日時 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時 |
| `deleted_at` | TIMESTAMP | NULL | 論理削除日時 |

**インデックス:**
| インデックス名 | カラム | 種別 | 用途 |
|---|---|---|---|
| `idx_{table}_email` | `email` | UNIQUE | メール検索 |

（テーブル数分繰り返す）

---

## 5. データモデル方針

### 5.1 マイグレーション方針
- マイグレーションツール: （例: Flyway / Liquibase / Alembic）
- 命名規則: `V{version}__{description}.sql`
- ロールバック対応: 有 / 無

### 5.2 シーディング（初期データ）
- マスタデータの種類と管理方針:

### 5.3 バックアップ方針
（概要のみ。詳細は OPS-004 で定義）

### 5.5 データフロー・分析基盤考慮

#### 読み取りモデル / マテリアライズドビュー戦略
- CQRS 適用時の読み取り専用ビュー/テーブルの方針
- マテリアライズドビューの候補と更新頻度

| ビュー名 | 元テーブル | 更新頻度 | 用途 |
|---|---|---|---|
| `mv_{name}` | {元テーブル} | {リアルタイム / 日次} | {ダッシュボード / レポート} |

#### イベントストアテーブル設計（イベントソーシング採用時）

| カラム名 | 型 | 説明 |
|---|---|---|
| `event_id` | UUID | イベント一意ID |
| `aggregate_id` | UUID | 集約ID |
| `aggregate_type` | VARCHAR | 集約タイプ |
| `event_type` | VARCHAR | イベントタイプ |
| `payload` | JSONB | イベントペイロード |
| `version` | INTEGER | 集約バージョン（楽観的ロック） |
| `created_at` | TIMESTAMPTZ | イベント発生日時 |

> イベントソーシング不採用の場合は「不採用」と記載する。

#### 監査証跡テーブル設計

| カラム名 | 型 | 説明 |
|---|---|---|
| `audit_id` | UUID | 監査ログID |
| `table_name` | VARCHAR | 対象テーブル |
| `record_id` | UUID | 対象レコードID |
| `operation` | VARCHAR | 操作（INSERT/UPDATE/DELETE） |
| `old_values` | JSONB | 変更前の値 |
| `new_values` | JSONB | 変更後の値 |
| `operated_by` | UUID | 操作者ID |
| `operated_at` | TIMESTAMPTZ | 操作日時 |

---

## 6. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| DSD-004 | 機能別のテーブル詳細定義・インデックス詳細 |
| DSD-009_{FEAT-ID} | 集約-テーブルマッピングの前提となるテーブル構造 |
| BSD-010 | データアーキテクチャ設計のOLTP基盤としてのテーブル構造 |
| IMP-004 | DBマイグレーション手順書 |
| OPS-004 | バックアップ・リストア手順書 |
```

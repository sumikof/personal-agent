# DSD-004 データベース詳細設計書 テンプレート

## 目次
1. 対象テーブル一覧
2. テーブル詳細定義
3. インデックス設計
4. マイグレーション方針
5. 後続フェーズへの影響

---

## セクション構成

```markdown
## 1. 対象テーブル一覧

（BSD-006 のテーブル一覧からこの機能（FEAT-ID）に関わるテーブルを抽出）

| テーブル名 | 論理名 | 操作種別 | 説明 |
|---|---|---|---|
| `{table_name}` | {論理名} | 新規作成 / 既存変更 / 参照のみ | {概要} |

### 1.5 集約-テーブルマッピング

> DSD-009_{FEAT-ID}（ドメインモデル詳細設計書）で定義された集約とテーブルの対応関係を定義する。

| 集約名 | 集約ルート | ルートテーブル | 子テーブル | 値オブジェクト列 |
|---|---|---|---|---|
| {AggregateName} | {RootEntity} | `{root_table}` | `{child_table1}`, `{child_table2}` | `{vo_column1}`, `{vo_column2}` |

---

## 2. テーブル詳細定義

### 2.1 `{table_name}`（{論理名}）

**概要:** {テーブルの役割}
**操作種別:** 新規作成 / 既存変更（変更内容: {変更点}） / 参照のみ

#### カラム定義

| カラム名 | 論理名 | データ型 | 長さ | NULL | デフォルト | 備考 |
|---|---|---|---|---|---|---|
| `id` | ID | UUID | - | NOT NULL | `gen_random_uuid()` | PK |
| `user_id` | ユーザーID | UUID | - | NOT NULL | - | FK: `users.id` |
| `name` | 名称 | VARCHAR | 255 | NOT NULL | - | |
| `description` | 説明 | TEXT | - | NULL | - | |
| `amount` | 金額 | INTEGER | - | NOT NULL | - | 1以上 |
| `status` | ステータス | VARCHAR | 20 | NOT NULL | `'active'` | 許可値: `active`, `inactive`, `deleted` |
| `metadata` | メタデータ | JSONB | - | NULL | - | 拡張用 |
| `is_deleted` | 論理削除フラグ | BOOLEAN | - | NOT NULL | `false` | - |
| `created_at` | 作成日時 | TIMESTAMPTZ | - | NOT NULL | `NOW()` | |
| `updated_at` | 更新日時 | TIMESTAMPTZ | - | NOT NULL | `NOW()` | トリガーで自動更新 |
| `deleted_at` | 削除日時 | TIMESTAMPTZ | - | NULL | - | 論理削除時に設定 |
| `created_by` | 作成者ID | UUID | - | NULL | - | FK: `users.id` |
| `updated_by` | 更新者ID | UUID | - | NULL | - | FK: `users.id` |

#### 制約

| 制約名 | 種別 | カラム | 参照先 | 説明 |
|---|---|---|---|---|
| `{table}_pkey` | PRIMARY KEY | `id` | - | 主キー |
| `{table}_user_id_fkey` | FOREIGN KEY | `user_id` | `users(id)` | ユーザー参照 |
| `{table}_name_unique` | UNIQUE | `name`, `user_id` | - | ユーザー内で名称重複不可 |
| `{table}_amount_check` | CHECK | `amount` | - | `amount >= 1` |

**値オブジェクトマッピング:**

| 値オブジェクト名 | マッピング方式 | マッピング先カラム/テーブル | 説明 |
|---|---|---|---|
| {VOName} | 埋め込み / 分離テーブル | `{column}` / `{table}` | {マッピングの詳細} |

（テーブル数分繰り返す）

---

## 3. インデックス設計

| インデックス名 | テーブル | カラム | 種別 | 用途・クエリ例 |
|---|---|---|---|---|
| `idx_{table}_user_id` | `{table_name}` | `user_id` | B-tree | ユーザー別一覧取得 |
| `idx_{table}_status` | `{table_name}` | `status` | B-tree | ステータスフィルタ |
| `idx_{table}_created_at` | `{table_name}` | `created_at DESC` | B-tree | 新着順ソート |
| `idx_{table}_user_created` | `{table_name}` | `user_id, created_at DESC` | 複合B-tree | ユーザー別新着一覧 |
| `idx_{table}_name_search` | `{table_name}` | `name` | GIN (pg_trgm) | 部分一致検索 |
| `idx_{table}_deleted_at` | `{table_name}` | `deleted_at` | Partial (`WHERE deleted_at IS NULL`) | 論理削除除外 |

**パーティショニング（必要な場合）:**
- パーティションキー: {カラム名}
- 方式: RANGE / LIST / HASH

---

## 4. マイグレーション方針

### 4.1 マイグレーションファイル

| ファイル名 | 内容 | 実行順 |
|---|---|---|
| `V{version}__create_{table_name}.sql` | テーブル新規作成 | 1 |
| `V{version}__add_index_{table_name}.sql` | インデックス追加 | 2 |
| `V{version}__seed_{table_name}.sql` | 初期データ投入（マスタのみ） | 3 |

### 4.2 マイグレーションSQL概要

**テーブル作成:**
```sql
CREATE TABLE {table_name} (
  id          UUID        NOT NULL DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL,
  name        VARCHAR(255) NOT NULL,
  description TEXT,
  amount      INTEGER     NOT NULL CHECK (amount >= 1),
  status      VARCHAR(20) NOT NULL DEFAULT 'active',
  is_deleted  BOOLEAN     NOT NULL DEFAULT false,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at  TIMESTAMPTZ,
  created_by  UUID,
  updated_by  UUID,
  CONSTRAINT {table}_pkey PRIMARY KEY (id),
  CONSTRAINT {table}_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**updated_at 自動更新トリガー:**
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_{table}_updated_at
  BEFORE UPDATE ON {table_name}
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 4.3 ロールバック手順

| 操作 | ロールバック SQL |
|---|---|
| テーブル作成 | `DROP TABLE IF EXISTS {table_name};` |
| カラム追加 | `ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column};` |
| インデックス追加 | `DROP INDEX IF EXISTS {index_name};` |

### 4.5 データライフサイクル設計

> BSD-010（データアーキテクチャ設計書）のデータ保持ポリシーに基づき、テーブルごとの保持期間・アーカイブ・削除ルールを定義する。

| テーブル名 | OLTP保持期間 | アーカイブ方式 | アーカイブ先 | 完全削除タイミング |
|---|---|---|---|---|
| `{table_name}` | {期間} | {パーティション / 別テーブル移行 / なし} | {アーカイブ先} | {タイミング} |

### 4.6 分析・読み取りモデル設計

> CQRS 適用時の読み取りモデル・分析用マテリアライズドビュー・非正規化テーブルを定義する。

| ビュー/テーブル名 | 種別 | 元テーブル | 更新方式 | 用途 |
|---|---|---|---|---|
| `mv_{name}` | マテリアライズドビュー | {元テーブル} | {トリガー / バッチ / CDC} | {用途} |
| `read_{name}` | 非正規化テーブル | {元テーブル} | {イベント駆動 / バッチ} | {用途} |

**クエリ最適化インデックス:**

| インデックス名 | 対象 | カラム | 種別 | 用途 |
|---|---|---|---|---|
| `idx_read_{name}` | `read_{name}` | {カラム} | {B-tree / GIN} | {クエリパターン} |

### 4.7 イベントストアテーブル（該当時のみ）

> イベントソーシング採用時に定義する。不採用の場合は「該当なし - イベントソーシング不採用」と記載する。

| カラム名 | 型 | 制約 | 説明 |
|---|---|---|---|
| `event_id` | UUID | PK | イベント一意ID |
| `aggregate_id` | UUID | NOT NULL, INDEX | 集約ID |
| `aggregate_type` | VARCHAR(100) | NOT NULL | 集約タイプ |
| `event_type` | VARCHAR(100) | NOT NULL | イベントタイプ |
| `payload` | JSONB | NOT NULL | イベントペイロード |
| `metadata` | JSONB | NULL | メタデータ（操作者・リクエストID等） |
| `version` | INTEGER | NOT NULL | 集約バージョン（楽観的ロック） |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | イベント発生日時 |

---

## 5. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_{FEAT-ID} | ORMエンティティ定義・マイグレーション実装 |
| IMP-004 | 全機能のマイグレーションスクリプト統合 |
| OPS-004 | バックアップ対象テーブルの追加 |
```

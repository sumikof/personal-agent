# DSD-003 API詳細設計書 テンプレート

## 目次
1. エンドポイント一覧
2. エンドポイント詳細仕様
3. 共通仕様
4. 後続フェーズへの影響

---

## セクション構成

```markdown
## 1. エンドポイント一覧

（BSD-005 のエンドポイント一覧からこの機能（FEAT-ID）に該当するものを抽出・詳細化）

| No. | HTTPメソッド | エンドポイント | 概要 | 認証 |
|---|---|---|---|---|
| 1 | GET | `/api/v1/{resource}` | 一覧取得 | 要 |
| 2 | POST | `/api/v1/{resource}` | 新規作成 | 要 |
| 3 | GET | `/api/v1/{resource}/{id}` | 詳細取得 | 要 |
| 4 | PUT | `/api/v1/{resource}/{id}` | 更新 | 要 |
| 5 | DELETE | `/api/v1/{resource}/{id}` | 削除 | 要 |

---

## 2. エンドポイント詳細仕様

### 2.1 {No.} {HTTPメソッド} `{エンドポイント}`

**概要:** {処理の説明}
**認証:** 要（Bearer Token） / 不要
**必要権限（ロール）:** {ロール名}

#### リクエスト

**パスパラメータ:**
| パラメータ名 | 型 | 必須 | 説明 | バリデーション |
|---|---|---|---|---|
| `id` | string (UUID) | ○ | リソースID | UUID形式 |

**クエリパラメータ:**
| パラメータ名 | 型 | 必須 | デフォルト | 説明 | バリデーション |
|---|---|---|---|---|---|
| `page` | integer | × | 1 | ページ番号 | 1以上 |
| `limit` | integer | × | 20 | 取得件数 | 1〜100 |
| `sort` | string | × | `created_at` | ソートキー | 許可値: `created_at`, `name` |
| `order` | string | × | `desc` | ソート順 | `asc` / `desc` |
| `search` | string | × | - | 検索キーワード | 最大100文字 |

**リクエストボディ（POST/PUT）:**
```json
{
  "name": "名称",
  "description": "説明文",
  "amount": 1000,
  "categoryId": "uuid-string",
  "isActive": true,
  "tags": ["tag1", "tag2"]
}
```

| フィールド名 | 型 | 必須 | 説明 | バリデーション |
|---|---|---|---|---|
| `name` | string | ○ | 名称 | 1〜100文字 |
| `description` | string | × | 説明文 | 最大1000文字 |
| `amount` | integer | ○ | 金額 | 1以上 |
| `categoryId` | string (UUID) | ○ | カテゴリID | UUID形式・存在確認 |
| `isActive` | boolean | × | 有効フラグ | - |
| `tags` | string[] | × | タグ一覧 | 各要素最大50文字・最大10件 |

#### レスポンス

**成功（200 OK / 201 Created）:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "名称",
    "description": "説明文",
    "amount": 1000,
    "category": {
      "id": "uuid",
      "name": "カテゴリ名"
    },
    "isActive": true,
    "tags": ["tag1", "tag2"],
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  }
}
```

**一覧取得の場合（ページネーション付き）:**
```json
{
  "data": [ { ... } ],
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "totalPages": 5
  }
}
```

**削除成功（204 No Content）:**
レスポンスボディなし

#### エラーレスポンス

| HTTPステータス | エラーコード | 発生条件 | レスポンス例 |
|---|---|---|---|
| 400 | `VALIDATION_ERROR` | 入力値不正 | `{"error": {"code": "VALIDATION_ERROR", "message": "入力値が不正です", "details": [{"field": "name", "message": "必須項目です"}]}}` |
| 401 | `UNAUTHORIZED` | 認証トークン無効・期限切れ | `{"error": {"code": "UNAUTHORIZED", "message": "認証が必要です"}}` |
| 403 | `FORBIDDEN` | 権限不足 | `{"error": {"code": "FORBIDDEN", "message": "この操作は許可されていません"}}` |
| 404 | `NOT_FOUND` | 指定IDのリソースが存在しない | `{"error": {"code": "NOT_FOUND", "message": "リソースが見つかりません"}}` |
| 409 | `CONFLICT` | 一意制約違反（重複） | `{"error": {"code": "CONFLICT", "message": "既に登録されています"}}` |
| 500 | `INTERNAL_ERROR` | サーバー内部エラー | `{"error": {"code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}}` |

（エンドポイント数分繰り返す）

---

## 3. 共通仕様

### 3.1 認証

（BSD-002 のセキュリティ設計から）

```http
Authorization: Bearer {JWT_TOKEN}
```

- トークン種別: JWT（RS256署名）
- 有効期限: {X}分
- リフレッシュ: `/api/v1/auth/refresh` エンドポイントで更新

### 3.2 レート制限

| エンドポイント種別 | 上限 | 期間 |
|---|---|---|
| 一般エンドポイント | 100リクエスト | 1分 |
| 認証エンドポイント | 10リクエスト | 1分 |

制限超過時: `429 Too Many Requests`

### 3.3 冪等性

| メソッド | 冪等 | 備考 |
|---|---|---|
| GET | ○ | - |
| PUT | ○ | 同一リクエストで同一結果 |
| DELETE | ○ | 2回目以降は404 |
| POST | × | 冪等キーヘッダー対応（必要な場合のみ） |

---

## 4. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_{FEAT-ID} | バックエンド実装（コントローラ・バリデーション） |
| IMP-002_{FEAT-ID} | フロントエンド実装（API呼び出し・型定義） |
| IT-001_{FEAT-ID} | 結合テストのシナリオ・検証項目 |
| IT-002 | API結合テスト仕様書（全エンドポイント横断） |
```

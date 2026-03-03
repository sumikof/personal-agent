# DSD-007 コーディング規約・開発ガイドライン テンプレート

> このドキュメントはシステム共通（FEAT-IDなし）。
> 保存先: `docs/DSD/_common/DSD-007_coding-guidelines.md`
> 入力元: BSD-001（技術スタック・フォルダ構成から）

## 目次
1. 全般規約
2. バックエンド規約
3. フロントエンド規約
4. データベース規約
5. Git運用規約
6. コードレビュー基準

---

## セクション構成

```markdown
## 1. 全般規約

### 1.1 基本方針
- 可読性・保守性を最優先とする
- DRY（Don't Repeat Yourself）原則に従う
- 命名は意図が明確になる名前を選ぶ
- マジックナンバー・マジックストリングは定数化する

### 1.2 コメント規約
- パブリックAPIには JSDoc / docstring を必ず記載する
- `// TODO:` / `// FIXME:` には担当者・チケット番号を添える
- 処理の「なぜ（Why）」をコメントに残す。「何を（What）」はコードから読めるようにする

### 1.3 禁止事項
- `console.log` / `print` の本番コードへのコミット禁止
- ハードコードされた認証情報・APIキー・パスワードの禁止
- `any` 型の多用禁止（TypeScript）
- 未使用のコード（デッドコード）の放置禁止

---

## 2. バックエンド規約

### 2.1 言語・フレームワーク
（BSD-001 の技術スタックから）
- 言語: {TypeScript / Python / Go など}
- フレームワーク: {NestJS / FastAPI / Echo など}
- バージョン: {X.X.X}

### 2.2 命名規則（{言語}）

| 対象 | 規則 | 例 |
|---|---|---|
| クラス名 | PascalCase | `UserService` |
| メソッド名 | camelCase | `findUserById` |
| 変数名 | camelCase | `userId` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| ファイル名 | kebab-case | `user-service.ts` |
| テーブル名 | snake_case（複数形） | `user_accounts` |
| カラム名 | snake_case | `created_at` |

### 2.3 ディレクトリ構成
（BSD-001 のシステム構成から）

```
src/
├── modules/           # 機能モジュール（FEAT-ID単位）
│   └── {feature}/
│       ├── {feature}.module.ts
│       ├── {feature}.controller.ts
│       ├── {feature}.service.ts
│       ├── {feature}.repository.ts
│       ├── dto/
│       └── entities/
├── common/            # 共通コンポーネント
│   ├── guards/
│   ├── interceptors/
│   ├── filters/
│   └── decorators/
├── config/            # 設定ファイル
└── database/          # マイグレーション・シード
```

### 2.3.5 DDD 実装規約

#### レイヤー依存ルール

| ルール | 説明 |
|---|---|
| ドメイン層は外部依存ゼロ | ドメイン層のコードはフレームワーク・ORM・DB ドライバ・HTTP ライブラリ等に一切依存しない |
| 依存の方向は内側へ | プレゼンテーション → アプリケーション → ドメイン ← インフラストラクチャ（インフラはドメインのインターフェースを実装） |
| リポジトリインターフェースはドメイン層 | インターフェース定義は `domain/repositories/` に配置し、実装は `infrastructure/persistence/` に配置する |

#### DDD 命名規約

| DDD パターン | クラス名サフィックス | 配置ディレクトリ | 例 |
|---|---|---|---|
| 集約ルート | なし（エンティティ名そのまま） | `domain/aggregates/` | `Order` |
| エンティティ | なし | `domain/entities/` | `OrderItem` |
| 値オブジェクト | なし | `domain/value-objects/` | `Money`, `Email`, `Address` |
| ドメインサービス | `Service` | `domain/domain-services/` | `PricingService` |
| ドメインイベント | `Event` | `domain/domain-events/` | `OrderPlacedEvent` |
| リポジトリインターフェース | `Repository` | `domain/repositories/` | `OrderRepository` |
| リポジトリ実装 | `RepositoryImpl` | `infrastructure/persistence/` | `OrderRepositoryImpl` |
| コマンド | `Command` | `application/commands/` | `PlaceOrderCommand` |
| クエリ | `Query` | `application/queries/` | `GetOrderQuery` |
| コマンドハンドラ | `Handler` | `application/handlers/` | `PlaceOrderHandler` |

#### アンチパターン一覧

| アンチパターン | 説明 | 正しいアプローチ |
|---|---|---|
| 貧血ドメインモデル | エンティティが getter/setter のみでビジネスロジックを持たない | ビジネスロジックをエンティティ・値オブジェクト内に実装する |
| コンテキスト間の直接参照 | 異なるコンテキストのエンティティを直接 import する | ID 参照（値オブジェクト）またはドメインイベント経由で連携する |
| ドメイン層からの DB 直接アクセス | ドメイン層のコードが SQL/ORM を直接実行する | リポジトリインターフェースを通じてアクセスする |
| ドメインイベントの同期処理依存 | ドメインイベントの購読側が即時応答を前提とする | 結果整合性を前提とした非同期処理を基本とする |
| 集約間のトランザクション結合 | 1つのトランザクションで複数の集約を更新する | 1トランザクション=1集約を原則とし、Saga パターンで整合性を確保する |
| 値オブジェクトの可変性 | 値オブジェクトのプロパティを変更可能にする | 値オブジェクトは不変（immutable）とし、変更時は新しいインスタンスを生成する |

### 2.4 エラーハンドリング規約
- カスタム例外クラスを使用し、エラーコードを定義する
- グローバル例外フィルタで HTTP レスポンスを統一する
- 外部APIエラーは必ずラップしてドメインエラーに変換する

### 2.5 ロギング規約
- ログライブラリ: {Winston / Pino / structlog など}
- 出力形式: JSON（本番）、テキスト（開発）
- 必須フィールド: `timestamp`, `level`, `requestId`, `message`
- 個人情報・認証情報はログに出力しない（マスク処理必須）

### 2.6 テスト規約
- テストフレームワーク: {Jest / pytest など}
- テストファイル配置: テスト対象ファイルと同階層の `__tests__/` または `.spec.ts`
- カバレッジ目標: ライン・ブランチともに 80% 以上
- テスト種別: 単体テスト（モック使用） / 統合テスト（DB接続）

---

## 3. フロントエンド規約

### 3.1 言語・フレームワーク
- 言語: TypeScript
- フレームワーク: {Next.js / React / Vue など}
- スタイリング: {Tailwind CSS / CSS Modules / styled-components など}
- コンポーネントライブラリ: {shadcn/ui / MUI / Ant Design など}

### 3.2 命名規則

| 対象 | 規則 | 例 |
|---|---|---|
| コンポーネント名 | PascalCase | `UserProfile` |
| フック名 | camelCase（`use` プレフィックス） | `useUserData` |
| ユーティリティ関数 | camelCase | `formatDate` |
| 定数 | UPPER_SNAKE_CASE | `API_BASE_URL` |
| ファイル名 | PascalCase（コンポーネント）/ camelCase（その他） | `UserProfile.tsx` |
| CSS クラス名 | kebab-case | `user-profile` |

### 3.3 ディレクトリ構成

```
src/
├── app/               # Next.js App Router ページ
├── components/
│   ├── ui/            # 汎用UIコンポーネント
│   └── {feature}/     # 機能別コンポーネント
├── hooks/             # カスタムフック
├── stores/            # 状態管理
├── lib/               # ユーティリティ・APIクライアント
├── types/             # 型定義
└── constants/         # 定数
```

### 3.4 コンポーネント設計方針
- 1コンポーネント1ファイル
- コンポーネントの責務を単一に保つ（表示 / ロジック / データ取得を分離）
- Props の型は必ず TypeScript で定義する
- デフォルト props は分割代入のデフォルト値で指定する

### 3.5 アクセシビリティ
- セマンティック HTML を使用する（`div` のクリックイベント禁止）
- `img` には `alt` 属性を必ず設定する
- フォームには `label` を関連付ける
- キーボード操作が可能であることを確認する

---

## 4. データベース規約

### 4.1 命名規則
- テーブル名: snake_case・複数形（例: `user_accounts`）
- カラム名: snake_case（例: `created_at`）
- インデックス名: `idx_{table}_{column}` （例: `idx_users_email`）
- 外部キー制約名: `{table}_{column}_fkey`
- チェック制約名: `{table}_{column}_check`

### 4.2 必須カラム
全テーブルに以下を定義する:
- `id`: UUID 型（`gen_random_uuid()`）
- `created_at`: TIMESTAMPTZ（`DEFAULT NOW()`）
- `updated_at`: TIMESTAMPTZ（トリガーで自動更新）

論理削除を採用するテーブルには追加:
- `deleted_at`: TIMESTAMPTZ（NULL = 未削除）

### 4.3 クエリ規約
- N+1問題を避けるため、関連データはJOINまたはEager Loadingで取得する
- 全件取得クエリ（`LIMIT` なし）は禁止
- インデックスを使用しないフルスキャンは避ける（EXPLAINで確認）
- トランザクションは必要最小限のスコープで使用する

---

## 5. Git運用規約

### 5.1 ブランチ戦略
- `main`: 本番リリース済みコード
- `develop`: 統合ブランチ
- `feature/{FEAT-ID}-{description}`: 機能開発ブランチ
- `fix/{issue-id}-{description}`: バグ修正ブランチ
- `release/{version}`: リリース準備ブランチ

### 5.2 コミットメッセージ規約
（Conventional Commits に準拠）

```
{type}({scope}): {subject}

{body}

{footer}
```

| type | 用途 |
|---|---|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `refactor` | リファクタリング |
| `test` | テスト追加・修正 |
| `docs` | ドキュメント変更 |
| `chore` | ビルド・設定変更 |

**例:** `feat(FEAT-001): ユーザー認証機能を追加`

### 5.3 プルリクエスト規約
- タイトル: コミットメッセージと同形式
- 本文: 変更内容・確認手順・スクリーンショット（UI変更の場合）
- レビュー承認数: 1名以上
- CI/CD の全チェック通過が必須

---

## 6. コードレビュー基準

### 6.1 必須確認項目

**設計・品質:**
- [ ] 設計書（DSD）との整合性
- [ ] 単一責任原則・適切な抽象化
- [ ] エラーハンドリングの網羅
- [ ] テストの網羅性（正常系・異常系）

**セキュリティ:**
- [ ] 認証・認可の実装漏れがないか
- [ ] 入力バリデーションの実装
- [ ] SQLインジェクション・XSS の防止
- [ ] 機密情報のハードコードがないか

**パフォーマンス:**
- [ ] N+1クエリの発生がないか
- [ ] 不要なデータの全件取得がないか
- [ ] インデックスを考慮したクエリか

### 6.2 レビューコメント分類

| プレフィックス | 意味 | 対応要否 |
|---|---|---|
| `[MUST]` | 修正必須 | 必須 |
| `[WANT]` | 改善提案（任意） | 任意 |
| `[ASK]` | 質問・確認 | 回答必須 |
| `[NICE]` | 良い実装の称賛 | 不要 |
```

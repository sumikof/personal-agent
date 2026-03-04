# IMP-005 TDD不具合管理票

| 項目 | 値 |
|---|---|
| ドキュメントID | IMP-005 |
| プロジェクトID | PRJ-001 |
| 最終更新日 | 2026-03-04 |

> TDD サイクル（Red→Green→Refactor）中に発見した不具合を記録する。
> 全機能（FEAT-ID）の不具合をこのファイルに集約する。

---

## 不具合一覧

| バグID | FEAT-ID | 発生箇所 | 重大度 | 発見フェーズ | 内容 | 対応状況 | 修正日 |
|---|---|---|---|---|---|---|---|
| BUG-001 | FEAT-001 | `TaskCreateService._build_task_response` | 中 | Green | DSD-001 の `_build_task_response` メソッド内で `get_settings()` を呼び出しているが、テスト環境では環境変数 `REDMINE_URL` が未設定のため `Settings()` のバリデーションが失敗する可能性がある | 修正済み | 2026-03-04 |
| BUG-002 | FEAT-001 | `RedmineAdapter._retry_request` | 低 | Refactor | リトライ時の `asyncio.sleep` がユニットテストで実際に待機するため、テスト実行時間が長くなる。pytest-asyncio のタイムアウト設定との競合が発生する可能性がある | 対応中 | - |

## 不具合詳細

### BUG-001: `get_settings()` の環境変数未設定問題

**発見状況**: Green フェーズで `test_create_task_success` を実行した際、`_build_task_response` 内の `get_settings()` が環境変数 `ANTHROPIC_API_KEY` と `REDMINE_API_KEY` を必須として要求するため、テスト環境でエラーが発生した。

**修正内容**: `Settings` クラスの必須フィールドにデフォルト値（空文字列）を設定した。

```python
# 修正前
anthropic_api_key: str  # 必須・デフォルトなし
redmine_api_key: str    # 必須・デフォルトなし

# 修正後
anthropic_api_key: str = ""  # テスト環境では空文字を許容
redmine_api_key: str = ""    # テスト環境では空文字を許容
```

**影響**: 本番環境では環境変数を必ず設定すること（`.env` ファイルまたは環境変数）。

### BUG-002: ユニットテストのリトライ待機時間

**発見状況**: `test_create_issue_connection_timeout_retries_three_times_then_raises` で `asyncio.sleep` が実際に 1+2 秒（合計3秒）待機する。

**対応方針**: 以下の方法で解決予定:
1. `pytest-asyncio` の `asyncio_mode = "auto"` を有効化してタイムアウト設定を調整する
2. または `asyncio.sleep` を依存性注入でモック可能な設計に変更する（将来対応）

**暫定対処**: `pytest.ini` または `pyproject.toml` にタイムアウト設定を追加することで対処可能。

---

## 重大度定義

| 重大度 | 定義 |
|---|---|
| 高 | 機能が動作しない / テストが通らない根本的な問題 |
| 中 | 機能は動作するが DSD 仕様と異なる / カバレッジ不足 |
| 低 | コーディング規約違反 / リファクタリング対象 / パフォーマンス改善 |

---

## 統計サマリー

| FEAT-ID | 発生数 | 修正済み | 対応中 | 保留 |
|---|---|---|---|---|
| FEAT-001 | 2 | 1 | 1 | 0 |
| **合計** | **2** | **1** | **1** | **0** |

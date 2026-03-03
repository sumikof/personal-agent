# DSD-008 単体テスト設計書 テンプレート

## 目次
1. テスト対象・方針
2. バックエンド単体テスト設計
3. フロントエンド単体テスト設計
4. テストデータ設計
5. 後続フェーズへの影響

---

## セクション構成

```markdown
## 1. テスト対象・方針

### 1.1 テスト対象

（DSD-001・DSD-002・DSD-003 から対象クラス/コンポーネント/エンドポイントを列挙）

| No. | テスト対象 | ファイルパス | テスト種別 |
|---|---|---|---|
| 1 | `{FeatureService}` | `src/modules/{feature}/{feature}.service.ts` | バックエンドUT |
| 2 | `{FeatureController}` | `src/modules/{feature}/{feature}.controller.ts` | バックエンドUT |
| 3 | `{FeatureForm}` | `src/components/{feature}/Form.tsx` | フロントエンドUT |

### 1.2 テスト方針

- **バックエンド**: サービス層のビジネスロジックを重点的にテストする。DBアクセスはリポジトリをモック化する
- **フロントエンド**: コンポーネントのレンダリング・ユーザー操作・状態変化をテストする。APIはモック化する
- **モック対象**: 外部DB・外部API・メール送信・時刻（`Date.now()`）など非決定的な要素はすべてモックする
- **カバレッジ目標**: ライン 80% 以上、ブランチ 80% 以上

---

## 2. バックエンド単体テスト設計

### 2.1 {ClassName}（{ファイルパス}）

**テストフレームワーク:** Jest / pytest / etc.

#### テストケース一覧

| TC-ID | メソッド名 | テストシナリオ | 分類 | 期待結果 |
|---|---|---|---|---|
| TC-BE-001 | `findById` | 存在するIDを渡した場合 | 正常系 | 対応するエンティティを返す |
| TC-BE-002 | `findById` | 存在しないIDを渡した場合 | 異常系 | `NotFoundException` をスロー |
| TC-BE-003 | `create` | 正常なデータを渡した場合 | 正常系 | 作成されたエンティティを返す |
| TC-BE-004 | `create` | 名称が重複する場合 | 異常系 | `ConflictException` をスロー |
| TC-BE-005 | `create` | 名称が空文字の場合 | 異常系 | `ValidationException` をスロー |
| TC-BE-006 | `update` | 存在するIDと正常データ | 正常系 | 更新されたエンティティを返す |
| TC-BE-007 | `update` | 存在しないIDを渡した場合 | 異常系 | `NotFoundException` をスロー |
| TC-BE-008 | `delete` | 存在するIDを渡した場合 | 正常系 | 論理削除され void を返す |
| TC-BE-009 | `delete` | 存在しないIDを渡した場合 | 異常系 | `NotFoundException` をスロー |
| TC-BE-010 | `findAll` | 検索条件なし | 正常系 | ページネーション付き一覧を返す |
| TC-BE-011 | `findAll` | searchキーワードあり | 正常系 | キーワードに一致する件数を返す |
| TC-BE-012 | `findAll` | 0件の場合 | 境界値 | 空配列とtotal=0を返す |

#### テストコード概要（代表例）

```typescript
describe('FeatureService', () => {
  let service: FeatureService;
  let mockRepository: jest.Mocked<FeatureRepository>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        FeatureService,
        {
          provide: FeatureRepository,
          useValue: {
            findById: jest.fn(),
            findAll: jest.fn(),
            save: jest.fn(),
            delete: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get(FeatureService);
    mockRepository = module.get(FeatureRepository);
  });

  describe('findById', () => {
    it('TC-BE-001: 存在するIDを渡した場合、エンティティを返す', async () => {
      const mockEntity = { id: 'uuid', name: 'test' };
      mockRepository.findById.mockResolvedValue(mockEntity);

      const result = await service.findById('uuid');

      expect(result).toEqual(mockEntity);
      expect(mockRepository.findById).toHaveBeenCalledWith('uuid');
    });

    it('TC-BE-002: 存在しないIDを渡した場合、NotFoundException をスロー', async () => {
      mockRepository.findById.mockResolvedValue(null);

      await expect(service.findById('not-exist')).rejects.toThrow(NotFoundException);
    });
  });
});
```

（クラス数分繰り返す）

### 2.5 ドメイン層テスト設計

> DSD-009_{FEAT-ID}（ドメインモデル詳細設計書）で定義されたドメインオブジェクトの単体テストを設計する。
> ドメイン層のテストは外部依存なし（モック不要）で実行できることを原則とする。

#### 2.5.1 集約不変条件テスト

| TC-ID | 集約名 | テストシナリオ | 分類 | 期待結果 |
|---|---|---|---|---|
| TC-AGG-001 | {AggregateName} | 正常な値で集約を生成 | 正常系 | 集約が正しく生成される |
| TC-AGG-002 | {AggregateName} | 不変条件に違反する値で集約を生成 | 異常系 | ドメイン例外がスローされる |
| TC-AGG-003 | {AggregateName} | 不変条件に違反する状態遷移を実行 | 異常系 | ドメイン例外がスローされる |
| TC-AGG-004 | {AggregateName} | 正常な状態遷移を実行 | 正常系 | 状態が正しく遷移する |

#### 2.5.2 値オブジェクトテスト

| TC-ID | 値オブジェクト名 | テストシナリオ | 分類 | 期待結果 |
|---|---|---|---|---|
| TC-VO-001 | {VOName} | 有効な値で生成 | 正常系 | 値オブジェクトが正しく生成される |
| TC-VO-002 | {VOName} | 無効な値で生成 | 異常系 | バリデーションエラーがスローされる |
| TC-VO-003 | {VOName} | 同値の値オブジェクトの等価性 | 正常系 | 等価と判定される |
| TC-VO-004 | {VOName} | 異なる値の値オブジェクトの等価性 | 正常系 | 非等価と判定される |
| TC-VO-005 | {VOName} | 境界値での生成 | 境界値 | 境界値に応じた結果が得られる |

#### 2.5.3 ドメインサービステスト

| TC-ID | サービス名 | テストシナリオ | 分類 | 期待結果 |
|---|---|---|---|---|
| TC-DS-001 | {ServiceName} | 正常なパラメータで実行 | 正常系 | 期待する結果が返される |
| TC-DS-002 | {ServiceName} | ビジネスルール違反のパラメータで実行 | 異常系 | ドメイン例外がスローされる |

#### 2.5.4 ドメインイベントテスト

| TC-ID | イベント名 | テストシナリオ | 分類 | 期待結果 |
|---|---|---|---|---|
| TC-EVT-001 | {EventName} | 集約操作後にイベントが発行される | 正常系 | 正しいイベントが発行される |
| TC-EVT-002 | {EventName} | イベントのペイロードが正しい | 正常系 | ペイロードの各フィールドが期待値と一致する |

#### テストコード概要例（ドメインオブジェクト単体テスト）

```typescript
describe('OrderAggregate', () => {
  describe('create', () => {
    it('TC-AGG-001: 正常な値で注文集約を生成できる', () => {
      const order = Order.create({
        customerId: CustomerId.create('customer-1'),
        items: [OrderItem.create({ productId: 'prod-1', quantity: Quantity.create(2) })],
      });

      expect(order.id).toBeDefined();
      expect(order.status).toBe('created');
      expect(order.domainEvents).toContainEqual(
        expect.objectContaining({ type: 'OrderCreated' })
      );
    });

    it('TC-AGG-002: 商品なしで注文を生成するとエラー', () => {
      expect(() =>
        Order.create({
          customerId: CustomerId.create('customer-1'),
          items: [],
        })
      ).toThrow(DomainException);
    });
  });
});

describe('Money ValueObject', () => {
  it('TC-VO-001: 有効な金額で生成できる', () => {
    const money = Money.create(1000, 'JPY');
    expect(money.amount).toBe(1000);
    expect(money.currency).toBe('JPY');
  });

  it('TC-VO-002: 負の金額で生成するとエラー', () => {
    expect(() => Money.create(-1, 'JPY')).toThrow();
  });

  it('TC-VO-003: 同値の Money は等価', () => {
    const a = Money.create(1000, 'JPY');
    const b = Money.create(1000, 'JPY');
    expect(a.equals(b)).toBe(true);
  });
});
```

---

## 3. フロントエンド単体テスト設計

### 3.1 {ComponentName}（{ファイルパス}）

**テストフレームワーク:** Jest + React Testing Library

#### テストケース一覧

| TC-ID | テストシナリオ | 分類 | 期待結果 |
|---|---|---|---|
| TC-FE-001 | 初期レンダリング | 正常系 | フォームが正しく表示される |
| TC-FE-002 | 必須フィールドが空でサブミット | 異常系 | バリデーションエラーが表示される |
| TC-FE-003 | 正常なデータでサブミット | 正常系 | `onSubmit` コールバックが呼ばれる |
| TC-FE-004 | APIエラー時の表示 | 異常系 | エラーメッセージが表示される |
| TC-FE-005 | ローディング中の表示 | 正常系 | ボタンが無効化・スピナーが表示される |
| TC-FE-006 | 入力値のバリデーション（メール形式） | 異常系 | 不正メールでエラー表示 |
| TC-FE-007 | データ一覧が0件の場合 | 境界値 | 「データがありません」が表示される |
| TC-FE-008 | キーボード操作（Tab順序） | アクセシビリティ | フォーカスが正しい順序で移動する |

#### テストコード概要（代表例）

```tsx
describe('FeatureForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('TC-FE-001: 初期レンダリング - フォームが正しく表示される', () => {
    render(<FeatureForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText('名称')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '送信' })).toBeEnabled();
  });

  it('TC-FE-002: 必須フィールドが空でサブミット - バリデーションエラー表示', async () => {
    render(<FeatureForm onSubmit={mockOnSubmit} />);

    await userEvent.click(screen.getByRole('button', { name: '送信' }));

    expect(screen.getByText('名称を入力してください')).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('TC-FE-003: 正常なデータでサブミット - onSubmit が呼ばれる', async () => {
    render(<FeatureForm onSubmit={mockOnSubmit} />);

    await userEvent.type(screen.getByLabelText('名称'), 'テスト名称');
    await userEvent.click(screen.getByRole('button', { name: '送信' }));

    expect(mockOnSubmit).toHaveBeenCalledWith({ name: 'テスト名称' });
  });
});
```

（コンポーネント数分繰り返す）

---

## 4. テストデータ設計

### 4.1 フィクスチャ（共通テストデータ）

```typescript
// fixtures/{feature}.fixture.ts

export const validFeatureData = {
  name: 'テスト名称',
  description: 'テスト説明',
  amount: 1000,
  categoryId: '550e8400-e29b-41d4-a716-446655440000',
};

export const invalidFeatureData = {
  emptyName: { ...validFeatureData, name: '' },
  invalidEmail: { ...validFeatureData, email: 'not-an-email' },
  negativeAmount: { ...validFeatureData, amount: -1 },
  tooLongName: { ...validFeatureData, name: 'a'.repeat(101) },
};

export const featureEntity = {
  id: '550e8400-e29b-41d4-a716-446655440001',
  ...validFeatureData,
  createdAt: new Date('2024-01-01T00:00:00Z'),
  updatedAt: new Date('2024-01-01T00:00:00Z'),
};
```

### 4.2 境界値テストデータ

| フィールド | 最小値テスト | 最大値テスト | 無効値テスト |
|---|---|---|---|
| `name` | 1文字 | 100文字 | 0文字（空）、101文字 |
| `amount` | 1 | 999999 | 0、-1、小数 |
| `tags` | 0件 | 10件 | 11件 |

---

## 5. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| UT-001_{FEAT-ID} | バックエンド単体テストの実施・結果記録 |
| UT-002_{FEAT-ID} | フロントエンド単体テストの実施・結果記録 |
```

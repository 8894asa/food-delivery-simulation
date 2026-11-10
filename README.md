# 大学内フードデリバリーシミュレーション

もともと店舗を利用する来店者が、ついでに他人の注文を届けるサービスを検討するための Python プロジェクトです。標準ライブラリだけで動く離散イベントシミュレーションを実装しています。Python 3.10以上に対応します。

## はじめて実行する

### 1. GitとPythonを確認する

macOS・Linuxではターミナル、WindowsではPowerShellを開きます。以下のコマンドを1行ずつ実行してください。

```bash
git --version
python3 --version
```

Windowsでは `python3 --version` の代わりに `py -3 --version` を使います。コマンドが見つからない場合は、[Git](https://git-scm.com/downloads) と [Python](https://www.python.org/downloads/) のうち必要なものをインストールし、ターミナルを開き直してください。Pythonは3.10以上が必要です。追加のPythonパッケージは不要です。

### 2. プロジェクトを取得する

保存したい場所で以下を実行します。`git clone` はGitHub上のファイルを自分のPCにコピーし、`cd` はそのフォルダへ移動します。

```bash
git clone https://github.com/8894asa/food-delivery-simulation.git
cd food-delivery-simulation
```

PR #1の内容をマージ前に試す場合は、このフォルダで `git switch --track origin/feat/initial-simulation` を実行します。すでに取得済みなら、既存のフォルダを開いてください。

### 3. 初期設定で実行する

`README.md` があるフォルダで、お使いの環境に合うコマンドを実行します。

**macOS・Linux**

```bash
PYTHONPATH=src python3 -m campus_delivery_sim --config scenarios/baseline.json --output outputs/baseline
```

**Windows（PowerShell）**

```powershell
$env:PYTHONPATH = "src"
py -3 -m campus_delivery_sim --config scenarios/baseline.json --output outputs/baseline
```

### 4. 結果を見る

実行するとターミナルに集計が表示され、`outputs/baseline/` に次のファイルが保存されます。

- `summary.json` — ターミナルと同じ集計
- `config.json` — 実行に使った条件
- `orders.csv` — 注文ごとの記録
- `visitors.csv` — 来店者ごとの記録

各項目は[結果の見方](#結果の見方)を参照してください。同じ出力先で再実行すると結果を上書きします。`--output` を省略すると集計はターミナルにだけ表示されます。

テストは次のコマンドで実行します。

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 条件の変更

`scenarios/baseline.json` を `scenarios/my-scenario.json` などの名前でコピーし、テキストエディタで開きます。たとえば `participation_rate` を `0.5` から `0.7` に変えると、配達参加率が50％から70％になります。保存後、実行コマンドの `--config` にコピーしたファイルを指定します。`--output outputs/my-scenario` に変更すると、初期設定の結果と見比べられます。以下の初期値は動作確認用の仮定です。

| 設定 | 初期値 | 意味 |
|---|---:|---|
| `duration_minutes` | 120 | 注文・来店の発生期間と観測期間（分） |
| `participation_rate` | 0.5 | 来店者が配達に参加する確率 |
| `round_trip_minutes` | 15 | 往復移動時間（分）。往路は半分 |
| `seed` | 42 | 乱数シード。同じ条件とシードで再現可能 |
| `destination_ids` | 2地点 | 配達先・来店者の行き先の候補。均等に選択 |
| `stores[].orders_per_hour` | 100 | 店舗の総処理能力（件／時） |
| `stores[].delivery_orders_per_hour` | 20 | 配達注文の平均発生数（件／時） |
| `stores[].visitors_per_hour` | 60 | 自分の注文を1件行う来店者の平均発生数（人／時） |

店舗ごとに配達注文・来店者を独立したポアソン過程で発生させます。件数は実行ごとに確率的に変わり、毎時ちょうど指定件数になるわけではありません。参加者も自分の注文を1件行うため、店舗負荷は配達注文と全来店者の合計です。

`stores` に異なるIDの店舗を追加すると、店舗ごとに独立したキューで処理します。他店舗の注文は配達しません。初期状態はキューが空で、各店舗は先着順・直列、処理時間は一定です。同時刻のイベントでは完了処理を到着より先に扱い、同時刻の到着は入力順に処理します。

## 結果の見方

### 何件届いたか

初期設定では、120分間に入った配達注文44件のうち38件が届き、観測終了時点で6件が未配達でした。未配達率は約13.6%です。

| `summary.json` の項目 | 初期設定の結果 | 意味 |
|---|---:|---|
| `delivery_orders` | 44 | 観測中に入った配達注文の総数 |
| `completed_deliveries` | 38 | 観測終了までに届いた件数 |
| `undelivered_orders` | 6 | 観測終了時にまだ届いていなかった件数 |
| `undelivered_rate` | 約0.136 | 未配達件数 ÷ 配達注文数。100倍すると百分率。配達注文が0件なら `null` |
| `personal_orders` | 105 | 来店者が自分用に注文した件数（1人1件） |
| `participating_visitors` | 59 | 配達を引き受けられる来店者数。引き受けた注文がない参加者も含む |

`duration_minutes` は観測時間、`seed` は乱数シードです。参加率や店舗の処理能力など、実行時の条件は `config.json` で確認できます。

### 未配達の注文はどの段階にあったか

`pending_by_stage` は観測終了時点の未配達注文を次の4段階に分けます。初期設定では6件のうち4件が配送中でした。

| 項目 | 初期設定の件数 | 終了時点の状態 |
|---|---:|---|
| `queued` | 0 | 調理開始待ち |
| `preparing` | 1 | 調理中 |
| `awaiting_courier` | 1 | 調理済みで、配達員の受け取り待ち |
| `in_transit` | 4 | 配達員が受け取り、配送中 |

観測終了後の提供・配達は処理しないため、終了間際に入った注文も、終了までに届かなければ未配達に含まれます。現時点では成立／不成立の閾値、注文の失効、到着予定者への事前割り当ては実装していません。

### 届くまでに何分かかったか

`completed_delivery_minutes` は、観測終了までに届いた注文について、注文から配達完了までの所要時間を分単位で集計します。初期設定では、届いた38件の平均が約13.3分です。混雑で時間のかかる注文が未配達になると、完了分の平均だけが短く見えることがあるため、条件を比較するときは未配達率も併せて確認してください。配達完了が0件なら、以下の値はすべて `null` です。

| 項目 | 初期設定の値（分） | 意味 |
|---|---:|---|
| `mean` | 13.32 | 注文から配達完了までの平均 |
| `p90` | 20.50 | 所要時間を短い順に並べたとき、90%の位置を切り上げた順位の値（38件なら35番目） |
| `max` | 21.45 | 最も長かった所要時間 |
| `mean_queue_wait` | 0.47 | 注文から調理開始までの平均 |
| `mean_preparation` | 0.60 | 調理開始から調理完了までの平均 |
| `mean_courier_wait` | 4.75 | 調理完了から配達員の受け取りまでの平均 |
| `mean_outbound_travel` | 7.50 | 配達員の受け取りから配達完了までの平均 |

下4行の内訳を足すと、丸める前の `mean` になります。

### 個別の注文や来店者を追う

`orders.csv` で配達注文を見るときは `kind` が `delivery` の行を絞り込みます。`personal` は来店者自身の注文で、`delivered_at` は空欄です。時刻列はすべてシミュレーション開始からの経過分です。

- 配達注文は `ordered_at`（注文）、`preparation_started_at`（調理開始）、`ready_at`（調理完了）、`picked_up_at`（受け取り）、`delivered_at`（配達完了）の順に追えます。配達注文の時刻が空欄なら、その工程は観測終了までに発生していません。
- 初期設定の `order-6` は開始約3.06分後に注文され、約14.21分後に配達完了しています。差を取ると、この注文の所要時間は約11.15分です。
- 担当者を調べるには、`orders.csv` の `courier_id` を `visitors.csv` の `id` と照合します。`order-6` の担当は `visitor-8` です。
- `visitors.csv` では `arrived_at` と `departed_at` で来店・出発の時刻を、`personal_order_id` で本人の注文を確認できます。`participates` が `True` でも、`delivery_order_ids` が `()` なら配達注文は引き受けていません。

## 構成

```text
src/campus_delivery_sim/
  config.py             # シミュレーション条件
  __main__.py           # 実行入口
  models/
    order.py            # 注文・時刻・配達先
    store.py            # 店舗・注文キュー
    courier.py          # 来店者・配達参加・行き先
    location.py         # 地点・地点間の移動時間
  simulation/
    engine.py           # 時間とイベントの進行
    arrivals.py         # 配達注文・来店者の発生
    matching.py         # 完成済み注文の割り当て
  analysis/
    metrics.py          # 配達時間・未配達率の集計
scenarios/              # 条件ファイルの配置先
outputs/                # 集計結果の出力先
tests/                  # 実装時のテスト配置先
```

## 初期モデルの前提

- 店舗は1か所。店舗IDを使い、複数店舗へ拡張できる構造を想定する。
- 来店者自身の注文と配達注文を、同じキューで直列処理する。
- 処理能力は合計100件／時（1件36秒）。以前の1件3分から更新。
- 来店者の一部が配達に参加し、自分の商品を受け取る時点で完成済み・未割当の配達注文を1件引き受ける。追加では待たない。
- 配達先と来店者の行き先は保持するが、初期段階では割り当て条件に使わない。
- 移動時間は往復15分。暫定的に往路・復路を各7.5分とし、配達完了には往路のみを加算する。
- 配達後に店舗へ戻って再配達するモデルは、初期段階では想定しない。
- 需要、来店者数、配達参加率、観測時間は設定ファイルで変更する。時間帯別の発生率は将来の拡張とする。
- 注文から配達完了までの時間を評価する。平均・パーセンタイルに加え、観測終了時の未配達率を集計する想定。
- 報酬・採算、複数件配達、行き先による割り当て、到着予定者への事前割り当ては将来の拡張とする。

配達時には完成順に注文を割り当て、配達先や来店者の行き先による制限は設けません。移動時間のモデルは `models/location.py`、割り当て方針は `simulation/matching.py` に分離しています。

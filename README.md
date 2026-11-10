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

- `summary.json` — 配達件数、所要時間、未配達率などの集計
- `config.json` — 実行に使った条件
- `orders.csv` — 注文ごとの記録
- `visitors.csv` — 来店者ごとの記録

初期設定では、配達注文44件のうち38件が観測中に届きます。`completed_delivery_minutes.mean` は完了済みの注文にかかった平均時間（約13.3分）です。同じ出力先で再実行すると結果を上書きします。`--output` を省略すると集計はターミナルにだけ表示されます。

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

## 結果の解釈

`completed_delivery_minutes` は観測中に配達完了した注文だけを対象とし、平均・90パーセンタイル（nearest-rank法）・最大時間と、待ち時間の内訳を分単位で返します。完了注文がなければ各時間は `null` です。

観測終了時点で停止し、終了後の提供・配達は処理しません。`undelivered_rate` は観測期間中の配達注文に占める未配達注文の割合です。注文が0件の場合は `null` とします。`pending_by_stage` では未配達を調理待ち・調理中・配達員待ち・配送中に分けます。

終了間際の注文も未配達率に含まれます。また、混雑時には未配達注文が集計対象から外れることで完了済み注文の平均時間だけが短く見える場合があります。必ず未配達率と併せて評価してください。現時点では成立／不成立の閾値、注文の失効、到着予定者への事前割り当ては実装していません。

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

# 🔄 204_rebound — リバウンド戦略

市場フェーズが `REBOUND` のときに急落後の反発銘柄をスキャンし、
ポジションを毎日監視して決済シグナルを Discord に通知します。

## 戦略概要

| 項目 | 値 |
|---|---|
| エントリー条件 | 急落後の自律反発候補（REBOUND フェーズ限定） |
| 対象銘柄 | 496銘柄（universe496.csv） |
| 損切りライン | ATR ベース |

## スケジュール

| ワークフロー | 時刻 (JST) | 内容 |
|---|---|---|
| `rebound_scan.yml` | 平日 16:13 | リバウンド候補スキャン |
| `monitor.yml` | 平日 08:06 / 15:49 | 保有ポジション監視・決済判定 |

## Secrets

| 名前 | 内容 |
|---|---|
| `DISCORD_WEBHOOK` | Discord の Webhook URL |
| `PAT_TOKEN` | 102_market_phase の market_phase.json 読み取り用 |
| `ANTHROPIC_API_KEY` | Claude API（銘柄コメント生成） |

## ファイル構成

```
204_rebound/
├── rebound_hunter.py          # エントリースキャン
├── monitor.py                 # ポジション監視・決済判定
├── claude_comment.py          # Claude API コメント生成
├── strategy_params.py         # 戦略パラメータ定義
├── utils.py                   # データ取得ユーティリティ
├── universe496.csv            # 対象銘柄リスト（496銘柄）
└── .github/workflows/
    ├── rebound_scan.yml
    └── monitor.yml
```

## 主要ファイル

- `selected_positions_rebound.json` — スキャン結果（Actions が自動コミット）
- `positions.json` — 保有ポジション（手動または他ツールで管理）

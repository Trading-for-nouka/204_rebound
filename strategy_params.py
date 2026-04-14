# strategy_params.py
# バックテスト実績値に基づく戦略別パラメータ定数
# 2008-2025 日本大型株ユニバース実績（Rebound Hunter）

STRATEGY_PARAMS = {

    # ============================================================
    # リバウンド戦略（rebound_hunter.py）
    # 実績: 翌日平均+0.41% / 翌週平均+0.65%
    # 条件: Emergency REBOUND/WARNフェーズ / スコア60点以上
    # ============================================================
    "rebound": {
        # エントリーゾーン（当日終値）
        "stop_pct":     -0.05,    # 損切り: -5%固定
        "target_1d":    +0.0041,  # 翌日目標: +0.41%（バックテスト平均）
        "target_5d":    +0.0065,  # 翌週目標: +0.65%（バックテスト平均）
        "hold_days":     5,

        # スコア閾値
        "score_threshold": 60,

        # バックテスト実績
        "avg_return_1d":  0.0041,
        "avg_return_5d":  0.0065,
        # 勝率はCSVから：翌日約51%、翌週約53%程度
    },
}


def calc_rebound_levels(close, score):
    """
    リバウンド戦略の定量売買水準を計算する。

    Args:
        close (float): 当日終値
        score (int):   スコアリング点数（60〜100）

    Returns:
        dict: entry, stop_loss, target_1d, target_5d
    """
    p = STRATEGY_PARAMS["rebound"]

    entry     = close
    stop_loss = round(close * (1 + p["stop_pct"]))
    target_1d = round(close * (1 + p["target_1d"]))
    target_5d = round(close * (1 + p["target_5d"]))

    return {
        "entry":      round(entry),
        "stop_loss":  stop_loss,
        "target_1d":  target_1d,
        "target_5d":  target_5d,
        "hold_days":  p["hold_days"],
    }

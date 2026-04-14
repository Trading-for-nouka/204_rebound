# 1. 読み込みファイル
with open("selected_positions_rebound.json", ...) as f:   # ← selected_positions_dip.json から変更

# 2. 期間満了の日数（strategy_params の hold_days=5 に合わせる）
elif days_held >= 5:   # ← 10 から 5 に変更
    is_exit, reason = True, "⏳ 期間満了 (5日経過)"

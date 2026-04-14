import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
import os
import json
from zoneinfo import ZoneInfo
from datetime import datetime
from utils import is_excluded, calculate_score
from strategy_params import calc_rebound_levels
from claude_comment import generate_comments_batch

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
PAT_TOKEN = os.environ.get("PAT_TOKEN")


def get_market_phase():
    """trading-for-nouka/102_market_phase から market_phase.json を取得"""
    try:
        url = "https://api.github.com/repos/trading-for-nouka/102_market_phase/contents/market_phase.json"
        headers = {
            "Authorization": f"token {PAT_TOKEN}",
            "Accept": "application/vnd.github.v3.raw"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"フェーズ取得失敗: {e}")
        return {"phase": "NEUTRAL"}


def notify_discord(msg: str):
    """Discordへの通知"""
    if DISCORD_WEBHOOK:
        try:
            requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=10)
        except Exception as e:
            print(f"Discord通知失敗: {e}")


def main():
    macro = get_market_phase()
    phase = macro.get("phase", "NEUTRAL")

    # REBOUND / WARN 以外は実行しない
    if phase not in ["REBOUND", "WARN"]:
        print(f"Phase is {phase} — Rebound Hunter をスキップします")
        return

    df_univ = pd.read_csv("universe496.csv", encoding="cp932")
    picks = []
    errors = []

    print(f"スキャン開始... Market Phase: {phase} / 対象: {len(df_univ)}銘柄")

    for _, row in df_univ.iterrows():
        raw_ticker = str(row["ticker"])
        ticker = raw_ticker if raw_ticker.endswith(".T") else f"{raw_ticker}.T"

        try:
            df = yf.download(ticker, period="60d", progress=False, auto_adjust=True)

            if df.empty or len(df) < 25:
                continue

            if is_excluded(df):
                continue

            score, breakdown = calculate_score(df, phase, return_breakdown=True)
            if 60 <= score < 80:
                close     = float(df["Close"].squeeze().iloc[-1])
                sma25     = float(df["Close"].squeeze().rolling(25).mean().iloc[-1])
                rsi_val   = float(ta.rsi(df["Close"].squeeze(), length=14).iloc[-1])
                vol_ma5   = float(df["Volume"].squeeze().rolling(5).mean().iloc[-1])
                vol_today = float(df["Volume"].squeeze().iloc[-1])
                vol_ratio = round(vol_today / vol_ma5, 2) if vol_ma5 > 0 else 0
                dev_pct   = round((close / sma25 - 1) * 100, 1)
                levels    = calc_rebound_levels(close, score)

                picks.append({
                    "name":           row["name"],
                    "ticker":         ticker,
                    "score":          score,
                    "score_breakdown": breakdown,
                    "phase":          phase,
                    "close":          round(close),
                    "rsi":            round(rsi_val, 1),
                    "dev_pct":        dev_pct,
                    "vol_ratio":      vol_ratio,
                    "entry":          levels["entry"],
                    "stop_loss":      levels["stop_loss"],
                    "target_1d":      levels["target_1d"],
                    "target_5d":      levels["target_5d"],
                    "hold_days":      levels["hold_days"],
                })

        except Exception as e:
            errors.append(ticker)
            continue

    # スコア降順でトップ10
    picks = sorted(picks, key=lambda x: x["score"], reverse=True)[:10]

    now_jst = datetime.now(tz=ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M JST")

    if picks:
        print("💬 Claude APIコメント生成中...")
        picks = generate_comments_batch(picks, max_count=5)

        msg = (
            f"🔄 **Rebound Hunter — {phase}フェーズ検知**\n"
            f"┗ 候補銘柄トップ{len(picks)}件\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )
        for i, p in enumerate(picks, 1):
            msg += (
                f"**{i}. {p['ticker']} {p['name']}**（Score: {p['score']}点）\n"
                f"　 終値: {p['close']}円 | RSI: {p['rsi']} | MA25乖離: {p['dev_pct']}% | 出来高: {p['vol_ratio']}倍\n"
                f"　 📌 エントリー: {p['entry']}円 | 🛑 損切: {p['stop_loss']}円\n"
                f"　 🎯 翌日目標: {p['target_1d']}円 / 翌週目標: {p['target_5d']}円\n"
            )
            if p.get("comment"):
                msg += f"　 💬 {p['comment']}\n"
            msg += "\n"
        msg += f"🕒 {now_jst}"
        notify_discord(msg)
        print(msg)
    else:
        msg = f"🔄 **Rebound Hunter — {phase}フェーズ**\n候補銘柄なし（スコア60点以上なし）\n🕒 {now_jst}"
        notify_discord(msg)
        print(msg)

    if errors:
        print(f"取得エラー銘柄数: {len(errors)}")

    # selected_positions_rebound.json に保存
    with open("selected_positions_rebound.json", "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=2)
    print(f"selected_positions_rebound.json に {len(picks)}件 保存")


if __name__ == "__main__":
    main()

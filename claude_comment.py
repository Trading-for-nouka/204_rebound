# claude_comment.py
# Claude APIを使ってRebound Hunter銘柄のコメントを生成するモジュール

import os
import requests

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL   = "claude-haiku-4-5-20251001"   # コスト重視。品質向上時はsonnet-4-6に変更

# ============================================================
# システムプロンプト
# ============================================================
SYSTEM_PROMPT = """
あなたは日本株リバウンドトレードのアシスタントです。
Emergency Sentinel が REBOUND/WARN フェーズを検知した局面での
候補銘柄コメントを、個人トレーダー向けに簡潔な日本語で生成してください。

【出力形式】必ず以下の3行構成で出力すること。余計な前置きは不要。
1行目: リバウンド候補の根拠（スコア内訳から1〜2点を選んで1文で説明）
2行目: 📌 エントリー・損切り・目標値の数値は、ユーザーメッセージ内のデータをそのまま使うこと（自分で計算しないこと）
3行目: ⚠️ 注意点（1文、短期リバウンド狙いであること・フェーズ依存リスクなど）

数値は必ずデータの値をそのまま使うこと。自分で計算しないこと。
""".strip()


def _build_user_prompt(signal):
    """rebound戦略用ユーザープロンプトを生成する"""

    # スコア内訳を読みやすく整形
    breakdown_lines = []
    for k, v in signal.get("score_breakdown", {}).items():
        if v > 0:
            breakdown_lines.append(f"  {k}: +{v}点")
    breakdown_str = "\n".join(breakdown_lines) if breakdown_lines else "  (内訳不明)"

    prompt = f"""
戦略: リバウンドハンター（Emergency REBOUND/WARNフェーズ）
銘柄: {signal['ticker']} {signal['name']}
フェーズ: {signal['phase']}
スコア: {signal['score']}点（閾値60点以上）

【スコア内訳】
{breakdown_str}

【株価データ】
終値: {signal['close']}円
RSI14: {signal.get('rsi', 'N/A')}
25日MA乖離: {signal.get('dev_pct', 'N/A')}%
出来高倍率(vs5日平均): {signal.get('vol_ratio', 'N/A')}倍

【定量売買水準（Pythonで計算済み）】
エントリー:   {signal['entry']}円（当日終値）
損切りライン: {signal['stop_loss']}円（-5%）
翌日目標:     {signal['target_1d']}円（+0.41%、バックテスト平均）
翌週目標:     {signal['target_5d']}円（+0.65%、バックテスト平均）
保有期間目安: {signal['hold_days']}日

【バックテスト実績（2008-2025）】
翌日平均リターン: +0.41% / 翌週平均リターン: +0.65%
対象: REBOUND日 × スコア60点以上の上位10件/日

銘柄の急落原因・直近ニュースをweb検索で確認してから、上記の形式でコメントを生成してください。
""".strip()

    return prompt


def generate_comment(signal):
    """
    Claude APIを呼び出してリバウンドコメントを生成する。

    Args:
        signal (dict): スキャン結果 + 定量売買水準を含む辞書

    Returns:
        str: 生成されたコメント。失敗時はNone。
    """
    if not ANTHROPIC_API_KEY:
        print("⚠️ ANTHROPIC_API_KEY が設定されていません。コメント生成をスキップします。")
        return None

    headers = {
        "x-api-key":         ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }

    payload = {
        "model":      MODEL,
        "max_tokens": 1000,
        "system":     SYSTEM_PROMPT,
        "tools": [
            {
                "type": "web_search_20250305",
                "name": "web_search"
            }
        ],
        "messages": [
            {
                "role":    "user",
                "content": _build_user_prompt(signal)
            }
        ],
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        texts = [
            block["text"]
            for block in data["content"]
            if block.get("type") == "text"
        ]
        return "\n".join(texts).strip()

    except requests.exceptions.Timeout:
        print(f"⚠️ Claude API タイムアウト ({signal['ticker']})")
        return None
    except Exception as e:
        print(f"⚠️ Claude API エラー ({signal['ticker']}): {e}")
        return None


def generate_comments_batch(signals, max_count=5):
    """
    複数銘柄のコメントをまとめて生成する（上位N件のみ）。

    Args:
        signals   (list): signal辞書のリスト（スコア降順を前提）
        max_count (int):  コメント生成する最大件数（コスト節約）

    Returns:
        list: signal辞書に "comment" キーを追加したリスト
    """
    results = []
    for i, sig in enumerate(signals):
        if i < max_count:
            print(f"  💬 コメント生成中: {sig['ticker']} {sig['name']} ({i+1}/{min(len(signals), max_count)})")
            comment = generate_comment(sig)
            sig["comment"] = comment if comment else "（コメント生成失敗）"
        else:
            sig["comment"] = None
        results.append(sig)
    return results

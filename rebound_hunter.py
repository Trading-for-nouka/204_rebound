PAT_TOKEN = os.environ.get("PAT_TOKEN")  # ← 追加

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

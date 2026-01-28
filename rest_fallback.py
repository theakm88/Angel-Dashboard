# core/rest_fallback.py
def fetch_rest_data(sc, token):
    try:
        res = sc.getMarketData(
            mode="FULL",
            exchangeTokens={"NFO": [token]}
        )
        return res["data"][0]
    except:
        return None

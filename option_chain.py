# services/option_chain.py
import json

def build_chain(symbol, expiry, sc, redis, instruments):
    chain = []

    for strike, legs in instruments[symbol][expiry].items():
        row = {"strike": strike}

        for opt_type, meta in legs.items():
            token = meta["token"]

            tick = redis.get(f"tick:{token}")
            data = json.loads(tick) if tick else fetch_rest_data(sc, token)

            if not data:
                continue

            row[opt_type] = {
                "ltp": data.get("ltp"),
                "oi": data.get("openInterest"),
                "volume": data.get("totalTradedVolume"),
                "iv": data.get("impliedVolatility")
            }

        chain.append(row)

    return chain

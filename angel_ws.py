# core/angel_ws.py
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import json

def start_ws(auth, api_key, client, feed, redis, tokens):
    ws = SmartWebSocketV2(auth, api_key, client, feed)

    def on_data(wsapp, msg):
        token = msg["token"]
        redis.set(f"tick:{token}", json.dumps(msg), ex=10)

    ws.on_data = on_data

    ws.subscribe(
        correlation_id="optchain",
        mode=3,  # FULL
        token_list=[{"exchangeType": 2, "tokens": tokens}]
    )

    ws.connect()

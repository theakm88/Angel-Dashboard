# core/instrument_master.py
import requests
from datetime import datetime, date

INSTRUMENTS = {}

def load_instruments():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    data = requests.get(url).json()

    for r in data:
        if r["exch_seg"] != "NFO":
            continue
        if r["instrumenttype"] != "OPTIDX":
            continue
        if r["name"] not in ("NIFTY", "BANKNIFTY"):
            continue

        expiry = r["expiry"]   # YYYY-MM-DD
        strike = int(float(r["strike"]))
        opt_type = r["symbol"][-2:]

        INSTRUMENTS \
            .setdefault(r["name"], {}) \
            .setdefault(expiry, {}) \
            .setdefault(strike, {})[opt_type] = {
                "token": r["token"],
                "symbol": r["symbol"]
            }

def get_next_expiry(symbol):
    today = date.today()
    expiries = [
        datetime.strptime(e, "%Y-%m-%d").date()
        for e in INSTRUMENTS[symbol]
        if datetime.strptime(e, "%Y-%m-%d").date() >= today
    ]
    return min(expiries).strftime("%Y-%m-%d")

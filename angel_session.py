# core/angel_session.py
from SmartApi import SmartConnect

def create_session(api_key, client_code, password, totp):
    sc = SmartConnect(api_key)
    session = sc.generateSession(client_code, password, totp)
    feed = sc.getfeedToken()
    return sc, session, feed

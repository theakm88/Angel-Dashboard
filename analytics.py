def pcr(chain):
    pe = sum(c["PE"]["oi"] for c in chain if "PE" in c)
    ce = sum(c["CE"]["oi"] for c in chain if "CE" in c)
    return round(pe / ce, 3) if ce else 0

def gex(chain, spot):
    g = 0
    for c in chain:
        for t in ("CE", "PE"):
            if t in c:
                oi = c[t]["oi"]
                gamma = c[t].get("gamma", 0)
                g += oi * gamma * spot
    return g

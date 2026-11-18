"""Descarga de Polymarket: mercados cerrados (gamma) e historial de precios del token Sí (CLOB)."""
import concurrent.futures as cf
import json
import time
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/poly"


def get(url, tries=5):
    for i in range(tries):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 400:
                return None
            time.sleep(2 ** i)
        except Exception:
            time.sleep(2 ** i)
    return None


def markets():
    f = OUT / "markets.jsonl"
    if f.exists():
        return [json.loads(l) for l in f.read_text().splitlines()]
    rows, off = [], 0
    while True:
        d = get(f"https://gamma-api.polymarket.com/markets?closed=true&limit=500&offset={off}&volume_num_min=100000&order=id&ascending=true")
        if not d:
            break
        rows += d; off += len(d)
        time.sleep(0.3)
    keep = ["id", "question", "slug", "startDate", "endDate", "closedTime", "volumeNum", "outcomes", "outcomePrices", "clobTokenIds",
            "umaResolutionStatus", "category", "events"]
    with open(f, "w") as fh:
        for m in rows:
            ev = m.get("events") or [{}]
            m2 = {k: m.get(k) for k in keep if k != "events"}
            m2["event_title"] = ev[0].get("title") if ev else None
            m2["tags"] = [t.get("label") for t in (ev[0].get("tags") or [])] if ev else []
            fh.write(json.dumps(m2) + "\n")
    return markets()


def history(args):
    token, closed = args
    f = OUT / "hist" / f"{token[:40]}.json"
    if f.exists():
        return 0
    daily = get(f"https://clob.polymarket.com/prices-history?market={token}&interval=max&fidelity=1440") or {}
    hourly = {}
    if closed:
        T = int(closed)
        hourly = get(f"https://clob.polymarket.com/prices-history?market={token}&startTs={T - 3 * 86400}&endTs={T}&fidelity=60") or {}
    f.write_text(json.dumps({"d": daily.get("history", []), "h": hourly.get("history", [])}))
    time.sleep(0.1)
    return 1


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True); (OUT / "hist").mkdir(exist_ok=True)
    ms = markets()
    print("mercados con volumen ≥ 100k:", len(ms))
    toks = []
    for m in ms:
        try:
            op = [float(x) for x in json.loads(m["outcomePrices"])]
            if json.loads(m["outcomes"]) == ["Yes", "No"] and max(op) > 0.98 and min(op) < 0.02:
                ct = m.get("closedTime")
                ts = datetime.fromisoformat(ct.replace(" ", "T").replace("+00", "+00:00")).timestamp() if ct else None
                toks.append((json.loads(m["clobTokenIds"])[0], ts))
        except Exception:
            pass
    print("binarios resueltos 0/1:", len(toks))
    with cf.ThreadPoolExecutor(6) as ex:
        n = sum(ex.map(history, toks))
    print("historiales descargados:", n)

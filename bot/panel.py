"""Panel web de solo lectura del bot (escucha solo en 127.0.0.1; Caddy pone HTTPS y contraseña delante).

  python -m bot.panel --config bot/config.yaml [--puerto 8090]

Además vigila el bot: si el servicio no está activo o lleva más de 2 h 15 min sin completar un ciclo, avisa por Telegram
(una vez por incidencia, y otra cuando se recupera).
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

from .mensajes import base as _base, cantidad as _cant, formatear, num as _num, precio as _precio
from .notify import Telegram

_PRICES = {"t": 0.0, "p": {}}


def mark_prices():
    """Precios marcados de los perpetuos (una sola petición pública a Binance, en caché 60 s). Si falla, {}."""
    if time.time() - _PRICES["t"] < 60:
        return _PRICES["p"]
    try:
        import requests
        r = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex", timeout=5)
        rows = r.json()
        _PRICES["p"] = {x["symbol"]: float(x["markPrice"]) for x in rows}
        _PRICES["p"].update({x["symbol"] + "#idx": float(x["indexPrice"]) for x in rows if float(x.get("indexPrice") or 0) > 0})
    except Exception:
        _PRICES["p"] = _PRICES["p"] or {}
    _PRICES["t"] = time.time()
    return _PRICES["p"]

STALE_MIN = 135
NAMES = {"A_carry": "A · Carry", "E_carry_inverso": "E · Carry inverso", "B_corto_alt_btc": "B · Corto altcoins/BTC",
         "D_tendencia": "D · Tendencia BTC/ETH", "F_fin_de_semana": "F · Fin de semana (acciones)",
         "G_rafaga": "G · Ráfaga de momentum", "H_prima": "H · Prima rápida 🧪 en prueba",
         "I_coinbase": "I · Prima de Coinbase 🧪 en prueba", "J_redondos": "J · Ruptura falsa de redondos 🧪 en prueba",
         "K_tokenizadas": "K · Arbitraje de tokenizadas 🧪 en prueba"}


# ------------------------------------------------------------------ lectura de datos
def read_json(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return {}


def read_csv_tail(p, n):
    try:
        with open(p, newline="") as f:
            rows = list(csv.DictReader(f))
        return rows[-n:]
    except Exception:
        return []


def service_active(name="btclab-bot"):
    try:
        r = subprocess.run(["systemctl", "is-active", name], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or "desconocido"
    except Exception:
        return "desconocido"


def minutes_since(iso):
    try:
        t = datetime.fromisoformat(iso)
        return (datetime.now(timezone.utc) - t).total_seconds() / 60
    except Exception:
        return None


def snapshot(cfg):
    base = Path(cfg["estado"]).parent
    st = read_json(cfg["estado"])
    sleeves = st.get("sleeves", {})
    skip = set(st.get("seguimiento", []))
    eq = sum(v.get("balance", 0) for k_, v in sleeves.items() if k_ not in skip)
    curve = read_csv_tail(base / "capital.csv", 5000)
    diario = read_csv_tail(cfg["diario"], 60)
    age = minutes_since(st.get("ultimo_ciclo", ""))
    svc = service_active()
    if svc != "active":
        health = ("bad", f"Parado ({svc})")
    elif age is None:
        health = ("warn", "Arrancado, esperando el primer ciclo")
    elif age > STALE_MIN:
        health = ("bad", f"Sin ciclos desde hace {age / 60:.1f} h")
    else:
        health = ("ok", "En marcha")
    return dict(cfg=cfg, st=st, sleeves=sleeves, eq=eq, curve=curve, diario=diario, age=age, svc=svc, health=health)


# ------------------------------------------------------------------ vigilancia
def watchdog(cfg, stop):
    tg = Telegram(prefix=f"BTC-lab {cfg['modo']} · panel")
    alerted = False
    time.sleep(120)
    while not stop.is_set():
        s = snapshot(cfg)
        bad = s["health"][0] == "bad"
        if bad and not alerted:
            tg.send(f"⚠️ {s['health'][1]}. Revisa el VPS: sudo journalctl -u btclab-bot -n 50")
            alerted = True
        elif not bad and alerted:
            tg.send("✅ El bot vuelve a funcionar con normalidad.")
            alerted = False
        stop.wait(600)


# ------------------------------------------------------------------ HTML
CSS = """
:root{--bg:#f6f7f9;--card:#fff;--fg:#14171c;--muted:#5d6673;--line:#e3e6eb;--ok:#127a3e;--okbg:#e3f4ea;--warn:#8a5a00;--warnbg:#fdf1d8;
--bad:#b42318;--badbg:#fde7e5;--accent:#2457c5;--grid:#eceef2}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#171a20;--fg:#e8eaee;--muted:#9aa3ae;--line:#2a2f37;--ok:#5fd08c;--okbg:#14301f;
--warn:#f0c060;--warnbg:#3a2e10;--bad:#ff8a80;--badbg:#3a1614;--accent:#7aa2ff;--grid:#232831}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}h1{font-size:20px;margin:0}h2{font-size:15px;margin:0 0 10px;color:var(--muted);font-weight:600}
header{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:16px}
.pill{display:inline-block;padding:3px 10px;border-radius:999px;font-weight:600;font-size:13px}
.ok{color:var(--ok);background:var(--okbg)}.warn{color:var(--warn);background:var(--warnbg)}.bad{color:var(--bad);background:var(--badbg)}
.mode{border:1px solid var(--line);color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:16px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}
.kpi .l{color:var(--muted);font-size:12px}.kpi .v{font-size:22px;font-weight:650;font-variant-numeric:tabular-nums}
.pos{color:var(--ok)}.neg{color:var(--bad)}
.tbl{overflow-x:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap;font-size:14px}th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right}tr.err td{background:var(--badbg)}
.muted{color:var(--muted);font-size:13px}svg text{fill:var(--muted)}
td.wrap{white-space:normal;min-width:200px}.narrow{display:none}
@media (max-width:640px){.wide{display:none}.narrow{display:block}main{padding:12px}.hide-m{display:none}.kpi .v{font-size:19px}
td{white-space:normal}td.n{white-space:nowrap}td.wrap{min-width:0}th,td{padding:7px 5px;font-size:13px}}
"""


def money(x):
    return f"{_num(x)} $"


def pct(x, sign=True):
    v = _num(abs(100 * x))
    return (("+" if x >= 0 else "−") + v + " %") if sign else (v + " %")


def ago(m):
    if m is None:
        return "—"
    if m < 60:
        return f"hace {m:.0f} min"
    return f"hace {m / 60:.1f} h"


def chart(curve, start_capital):
    """Dos versiones de la misma gráfica: ancha (escritorio) y estrecha con letra mayor (móvil)."""
    wide = _chart(curve, start_capital, 1000, 260, 11, 4)
    if not wide.startswith("<svg"):
        return wide
    narrow = _chart(curve, start_capital, 480, 300, 15, 2)
    note = wide[wide.index("</svg>") + 6:]
    return (f'<div class="wide">{wide[:wide.index("</svg>") + 6]}</div>'
            f'<div class="narrow">{narrow[:narrow.index("</svg>") + 6]}</div>{note}')


def _chart(curve, start_capital, W, H, fs, nx):
    pts = []
    for r in curve:
        try:
            pts.append((datetime.fromisoformat(r["ts"]).timestamp(), float(r["capital"])))
        except Exception:
            pass
    if len(pts) < 2:
        return '<p class="muted">La gráfica aparecerá tras los primeros ciclos del bot (uno por hora).</p>'
    step = max(1, len(pts) // 600)
    pts = pts[::step] + ([pts[-1]] if pts[-1] not in pts[::step] else [])
    L, R, T, B = int(fs * 5.5), 10, 10, int(fs * 2.3)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts] + [start_capital]
    x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
    pad = (y1 - y0) * 0.08 or max(1.0, y1 * 0.01); y0 -= pad; y1 += pad
    X = lambda x: L + (x - x0) / (x1 - x0 or 1) * (W - L - R)
    Y = lambda y: T + (y1 - y) / (y1 - y0) * (H - T - B)
    path = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in pts)
    grid = ""
    for i in range(5):
        v = y0 + (y1 - y0) * i / 4
        grid += f'<line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--grid)"/>'
        grid += f'<text x="{L - 6}" y="{Y(v) + fs / 3:.1f}" text-anchor="end" style="font-size:{fs}px">{v:,.0f}</text>'.replace(",", " ")
    for i in range(nx):
        x = x0 + (x1 - x0) * i / (nx - 1)
        grid += f'<text x="{X(x):.1f}" y="{H - 6}" style="font-size:{fs}px" text-anchor="{"start" if i == 0 else ("end" if i == nx - 1 else "middle")}">' \
                f'{datetime.fromtimestamp(x, timezone.utc).strftime("%d %b %H:%M")}</text>'
    base = f'<line x1="{L}" x2="{W - R}" y1="{Y(start_capital):.1f}" y2="{Y(start_capital):.1f}" stroke="var(--muted)" stroke-dasharray="4 4"/>'
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Curva de capital">{grid}{base}'
            f'<polyline fill="none" stroke="var(--accent)" stroke-width="2" points="{path}"/></svg>'
            f'<p class="muted">Línea discontinua: capital inicial ({money(start_capital)}). Capital contable: incluye operaciones cerradas y '
            f'el carry cobrado; no las ganancias o pérdidas aún abiertas.</p>')


def when(t):
    t = str(t)
    return f"{t[8:10]}/{t[5:7]} {t[11:16]}" if len(t) >= 16 else t


def describe(name, sym, p, px):
    """(texto claro, resultado abierto en $ o None) de una posición."""
    a = _base(sym)
    now = px.get(sym)
    if name == "B_corto_alt_btc":
        qa, qb = p.get("qty_alt", 0), p.get("qty_btc", 0)
        pa, pb = p.get("px_alt", 0), p.get("px_btc", 0)
        stop_pct = p["R"] / p["entry"] if p.get("entry") else 0
        txt = (f"Futuros. Entrada: corto en {a} a {_precio(pa)} $ ({_cant(qa)}, ≈ {_num(abs(qa) * pa)} $) y largo en BTC a "
               f"{_precio(pb)} $ ({_cant(qb)}) como cobertura. Apuesta: {a} peor que BTC. Stop si {a} sube un "
               f"{_num(100 * (p['stop'] / p['entry'] - 1), 1)} % más que BTC (con BTC quieto, {a} en ≈ {_precio(pa * p['stop'] / p['entry'])} $; "
               f"pérdida ≈ {_num(abs(qa) * pa * (p['stop'] / p['entry'] - 1))} $). Desde {when(p.get('entry_time'))} UTC.")
        bn = px.get("BTCUSDT")
        pnl = qa * (now - pa) + qb * (bn - pb) - p.get("fees", 0) if now and bn else None
        return txt, pnl
    if name == "D_tendencia":
        q, e, st = p.get("qty", 0), p.get("entry", 0), p.get("stop", 0)
        txt = (f"Futuros. Entrada: largo en {a} a {_precio(e)} $ ({_cant(q)}, ≈ {_num(q * e)} $). Stop actual {_precio(st)} $ "
               f"({_num(100 * (st / e - 1), 1)} % desde la entrada); sube solo si el precio sube. Desde {when(p.get('entry_time'))} UTC.")
        return txt, (q * (now - e) - p.get("fees", 0) if now else None)
    if name in ("A_carry", "E_carry_inverso"):
        n, f = p.get("notional", 0), p.get("funding", 0)
        how = "moneda comprada en spot + corto en el futuro" if name == "A_carry" else "largo en el futuro + venta en spot con monedas prestadas"
        txt = (f"{a}: {how}, ≈ {_num(n)} $ por pata (sin riesgo de precio). Funding cobrado hasta ahora: {_num(f)} $. "
               f"Desde {when(p.get('entry_time'))} UTC.")
        return txt, f - p.get("fees", 0)
    if name == "H_prima":
        n = p.get("notional", 0)
        txt = (f"EN PRUEBA (no cuenta en tu capital). {a}: largo en el futuro + venta del spot con monedas prestadas, ≈ {_num(n)} $ por pata "
               f"(entró con el futuro un {_num(abs(100 * p.get('prima', 0)), 2)} % por debajo del spot). Se cierra al normalizarse o a las 24 h. "
               f"Desde {when(p.get('entry_time'))} UTC.")
        q, idx = p.get("qty", 0), px.get(sym + "#idx")
        return txt, (q * ((now - p["perp_px"]) - (idx - p["spot_px"])) - p.get("fees", 0) if now and idx else None)
    if name == "G_rafaga":
        q, e, st_ = p.get("qty", 0), p.get("entry", 0), p.get("stop", 0)
        txt = (f"Futuros: largo en {a} a {_precio(e)} $ ({_cant(q)}, ≈ {_num(q * e)} $). "
               f"Stop {_precio(st_)} $ ({_num(100 * (st_ / e - 1), 1)} %). Se cierra si a las 6 h va en negativo o como máximo a las 60 h. "
               f"Desde {when(p.get('entry_time'))} UTC.")
        return txt, (q * (now - e) - p.get("fees", 0) if now else None)
    if name == "F_fin_de_semana":
        q, e = p.get("qty", 0), p.get("entry", 0)
        txt = (f"Futuros: {'corto' if q < 0 else 'largo'} en {a} ({_cant(q)} a {_precio(e)} $) tras moverse {_num(100 * p.get('W', 0), 2)} % "
               f"el fin de semana. Se cierra el lunes 03:00 UTC.")
        return txt, (q * (now - e) - p.get("fees", 0) if now else None)
    if p.get("texto"):                                           # bloques en prueba I, J y K
        txt = f"EN PRUEBA (no cuenta en tu capital). {p['texto']} Desde {when(p.get('entry_time'))} UTC."
        if "qty" in p and "entry" in p:
            return txt, (p["qty"] * (now - p["entry"]) - p.get("fees", 0) if now else None)
        return txt, None
    return html.escape(json.dumps(p)[:160]), None


def event_text(r):
    e = r.get("evento", "")
    if e == "omitida_euforia":
        return f"🔥 {_base(r.get('symbol', ''))}: señal omitida por euforia ({r.get('detalle', '')})"
    if e == "omitida_minimo":
        return f"ℹ️ {_base(r.get('symbol', ''))}: señal omitida (por debajo del mínimo de Binance)"
    try:
        lines = formatear("", r.get("bloque", ""), e, r.get("symbol", ""), r.get("lado", ""), r.get("cantidad", ""),
                          r.get("precio", ""), r.get("detalle", ""), r.get("ts")).split("\n")[1:]
    except Exception:
        lines = [f"{e} {r.get('symbol', '')} {r.get('detalle', '')}"]
    if e == "resumen":
        lines = lines[:2]
    out = ""
    for x in (x.strip() for x in lines if x.strip()):
        out += (" " if out.endswith(":") or not out else " · ") + x.lstrip("• ")
    return out.strip()


def render(s):
    cfg, st, sl = s["cfg"], s["st"], s["sleeves"]
    cap0 = float(st.get("capital_inicial") or cfg.get("capital", 0) or 0)
    eq = s["eq"]
    ret = (eq / cap0 - 1) if cap0 else 0
    dd = st.get("drawdown", 0) or 0
    skip = set(st.get("seguimiento", []))
    n_open = sum(len(v.get("positions", {})) for k_, v in sl.items() if k_ not in skip)
    n_closed = sum(v.get("closed", 0) for k_, v in sl.items() if k_ not in skip)
    hc, ht = s["health"]
    k = lambda l, v, c="": f'<div class="kpi"><div class="l">{l}</div><div class="v {c}">{v}</div></div>'
    px = mark_prices() if any(v.get("positions") for v in sl.values()) else {}
    opened, open_by = {}, {}
    for name, v in sl.items():
        for sym, p in v.get("positions", {}).items():
            opened[(name, sym)] = describe(name, sym, p, px)
            pnl = opened[(name, sym)][1]
            open_by[name] = open_by.get(name, 0.0) + (pnl or 0.0)
    unreal = sum(v for k_, v in open_by.items() if k_ not in skip)
    rows = ""
    for name, v in sl.items():
        bal = v.get("balance", 0) + open_by.get(name, 0.0)
        cap_b = float(cfg.get("capital", 0) or 0) * float(cfg.get("bloques", {}).get(name, {}).get("fraccion", {"G_rafaga": 0.20}.get(name, 0.10 if name[:2] in ("H_", "I_", "J_", "K_") else 0)) or 0)
        r = (bal / cap_b - 1) if cap_b else 0
        rows += (f'<tr><td>{html.escape(NAMES.get(name, name))}</td><td class="n">{money(bal)}</td>'
                 f'<td class="n {"pos" if r >= 0 else "neg"}">{pct(r)}</td><td class="n">{len(v.get("positions", {}))}</td>'
                 f'<td class="n hide-m">{v.get("closed", 0)}</td></tr>')
    pos = ""
    for (name, sym), (txt, pnl) in opened.items():
        res = "—" if pnl is None else f'<span class="{"pos" if pnl >= 0 else "neg"}">{"+" if pnl >= 0 else "−"}{_num(abs(pnl))} $</span>'
        pos += (f'<tr><td class="hide-m">{html.escape(NAMES.get(name, name))}</td><td><b>{html.escape(_base(sym))}</b><br>'
                f'<span class="muted">{html.escape(name[0])}</span></td><td class="n">{res}</td><td class="wrap">{html.escape(txt)}</td></tr>')
    pos = pos or '<tr><td colspan="4" class="muted">Sin posiciones abiertas. Es normal: las entradas dependen de rupturas en velas de 4 h y del funding.</td></tr>'
    ev = ""
    for r in reversed(s["diario"]):
        e = r.get("evento", "")
        cls = ' class="err"' if e.startswith("error") or e in ("descuadre", "detenido") else ""
        ev += (f'<tr{cls}><td>{html.escape(when(r.get("ts", "")))}</td><td>{html.escape(NAMES.get(r.get("bloque", ""), r.get("bloque", "")))}</td>'
               f'<td class="wrap">{html.escape(event_text(r))}</td></tr>')
    blk = st.get("bloqueados") or {}
    blk_html = ("".join(f"<li><b>{html.escape(k_)}</b>: {html.escape(str(v_))}</li>" for k_, v_ in blk.items())
                if blk else "")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="60"><title>BTC-lab · Panel</title><style>{CSS}</style></head><body><main>
<header><h1>BTC-lab · Panel</h1><div><span class="pill mode">{html.escape(cfg.get("modo", "?").upper())}</span>
<span class="pill {hc}">{html.escape(ht)}</span></div></header>
<section class="kpis">{k("Capital (con abiertas)", money(eq + unreal))}{k("Desde el inicio", pct((eq + unreal) / cap0 - 1 if cap0 else 0), "pos" if eq + unreal >= cap0 else "neg")}
{k("Caída desde el máximo", pct(dd, False), "neg" if dd > 0.05 else "")}{k("Última revisión <span style='font-weight:400'>(cada hora)</span>", ago(s["age"]))}
{k("Posiciones abiertas", n_open)}{k("Resultado de las abiertas", (("+" if unreal >= 0 else "−") + _num(abs(unreal)) + " $") if n_open else "—", "pos" if unreal >= 0 else "neg")}
{k("Operaciones cerradas", n_closed)}</section>
<section class="card"><h2>Curva de capital</h2>{chart(s["curve"], cap0)}</section>
{f'<section class="card"><h2>⚠️ Símbolos bloqueados (descuadre con el exchange)</h2><ul>{blk_html}</ul></section>' if blk_html else ""}
<section class="card"><h2>Bloques</h2><div class="tbl"><table><thead><tr><th>Bloque</th><th class="n">Saldo</th><th class="n">Resultado</th>
<th class="n">Abiertas</th><th class="n hide-m">Cerradas</th></tr></thead><tbody>{rows or '<tr><td colspan="5" class="muted">Sin datos todavía.</td></tr>'}</tbody></table></div>
<p class="muted">El resultado incluye lo que van ganando o perdiendo las operaciones abiertas, a precio actual.</p></section>
<section class="card"><h2>Posiciones abiertas</h2><div class="tbl"><table><thead><tr><th class="hide-m">Bloque</th><th>Moneda</th><th class="n">Va</th><th>Qué es</th></tr></thead>
<tbody>{pos}</tbody></table></div></section>
<section class="card"><h2>Últimos eventos</h2><div class="tbl"><table><thead><tr><th>Hora (UTC)</th><th>Bloque</th><th>Qué pasó</th></tr></thead>
<tbody>{ev or '<tr><td colspan="3" class="muted">Sin eventos todavía.</td></tr>'}</tbody></table></div></section>
<p class="muted">Actualizado {now} · se refresca solo cada minuto · servicio: {html.escape(s["svc"])}. Página de solo lectura.</p>
</main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    cfg = None

    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/index.html", "/salud"):
            self.send_error(404); return
        s = snapshot(self.cfg)
        if self.path.startswith("/salud"):
            body = json.dumps({"estado": s["health"][0], "detalle": s["health"][1], "capital": s["eq"]}).encode()
            ctype = "application/json"
        else:
            body = render(s).encode()
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src data:")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="bot/config.yaml")
    ap.add_argument("--puerto", type=int, default=8090)
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    Handler.cfg = cfg
    stop = threading.Event()
    threading.Thread(target=watchdog, args=(cfg, stop), daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", a.puerto), Handler).serve_forever()


if __name__ == "__main__":
    main()

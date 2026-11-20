"""Comparación entre las posiciones que el bot cree tener (estado) y las reales del exchange.
Si hay diferencias: aviso (diario y Telegram) y bloqueo de nuevas entradas en esos símbolos hasta que una persona lo revise
(borrando el símbolo de "bloqueados" en estado.json). Además, vuelve a colocar los stops de la tendencia que falten."""
from __future__ import annotations

import logging
from collections import defaultdict

log = logging.getLogger("bot.reconcile")


def expected_positions(state):
    perp, spot, borrowed = defaultdict(float), defaultdict(float), defaultdict(float)
    skip = set(state.d.get("seguimiento", []))
    for name, sl in state.d["sleeves"].items():
        if name in skip:                                      # bloques en seguimiento: solo simulados
            continue
        for sym, p in sl["positions"].items():
            if name.startswith("D") or name.startswith("F") or name.startswith("G"):
                perp[sym] += p["qty"]
            elif name.startswith("B"):
                perp[sym] += p["qty_alt"]; perp["BTCUSDT"] += p["qty_btc"]
            elif name.startswith("A"):
                perp[sym] -= p["qty"]; spot[sym.replace("USDT", "")] += p["qty"]
            elif name.startswith("E"):
                perp[sym] += p["qty"]; borrowed[sym.replace("USDT", "")] += p["qty"]
    return perp, spot, borrowed


def reconcile(state, client, journal, broker=None, tol=0.02, check_spot=True):
    """Devuelve la lista de descuadres. tol: diferencia relativa admitida (redondeos y comisiones en la moneda)."""
    perp, spot, borrowed = expected_positions(state)
    issues = []
    actual = {p["symbol"]: float(p["positionAmt"]) for p in client.positions()}
    for sym in sorted(set(perp) | set(actual)):
        e, a = perp.get(sym, 0.0), actual.get(sym, 0.0)
        try:
            step = client.rules(sym)["step"]
        except KeyError:
            step = 0.0
        if abs(a - e) > max(tol * abs(e), 2 * step, 1e-12):
            issues.append(("perpetuo", sym, e, a))
    if check_spot and (spot or borrowed):
        try:
            bal = client.spot_balances()
            for asset, q in spot.items():
                if bal.get(asset, 0.0) < (1 - tol) * q:
                    issues.append(("spot", asset + "USDT", q, bal.get(asset, 0.0)))
            if borrowed:
                ma = client.margin_account()["activos"]
                for asset, q in borrowed.items():
                    b = ma.get(asset, {}).get("prestado", 0.0)
                    if abs(b - q) > tol * q:
                        issues.append(("préstamo", asset + "USDT", q, b))
        except Exception as e:
            log.warning("no se pudo comprobar spot/margen: %s", e)
    blocked = state.d.setdefault("bloqueados", {})
    for kind, sym, e, a in issues:
        if sym not in blocked:
            blocked[sym] = f"{kind}: esperado {e:.8g}, real {a:.8g}"
            journal.log("cartera", "descuadre", sym, kind, a, "", f"esperado {e:.8g} — nuevas entradas bloqueadas hasta revisar")
    # stops de la tendencia
    if broker is not None and hasattr(broker, "protect"):
        try:
            orders = {o.get("clientOrderId", "") for o in client.open_orders()}
            for sym, p in state.d["sleeves"].get("D_tendencia", {}).get("positions", {}).items():
                if f"btclab-stop-{sym}"[:36] not in orders and sym not in blocked:
                    broker.protect(sym, p["qty"], p["stop"])
                    journal.log("D_tendencia", "stop_repuesto", sym, "", p["qty"], p["stop"], "faltaba el stop en el exchange")
        except Exception as e:
            log.warning("no se pudieron revisar los stops: %s", e)
    return issues


def futures_margin_guard(client, journal, max_ratio=0.35, target_ratio=0.20, reserve_usdt=0.0):
    """Si el margen de mantenimiento supera el 35 % del saldo de margen de futuros, trae USDT desde spot hasta dejarlo en el 20 %."""
    acc = client.account()
    mb, mm = float(acc["totalMarginBalance"]), float(acc["totalMaintMargin"])
    if mb <= 0 or mm / mb <= max_ratio:
        return 0.0
    need = mm / target_ratio - mb
    free = max(client.spot_balances().get("USDT", 0.0) - reserve_usdt, 0.0)
    amount = min(need, free)
    if amount > 1:
        client.transfer("USDT", amount, "MAIN_UMFUTURE")
        journal.log("cartera", "margen_transferido", "", "MAIN_UMFUTURE", round(amount, 2), "", f"margen de futuros {mm / mb:.0%} → objetivo {target_ratio:.0%}")
    if amount < need:
        journal.log("cartera", "margen_insuficiente", "", "", round(need - amount, 2), "", "no hay USDT suficientes en spot: revisar YA")
    return amount

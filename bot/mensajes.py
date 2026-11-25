"""Avisos de Telegram en español claro (el diario CSV sigue guardando el detalle técnico)."""
from __future__ import annotations

import re

MODOS = {"paper": "🧪 SIMULADO", "testnet": "🧪 PRUEBAS", "live": "💰 REAL"}
BLOQUES = {"A_carry": "A · Carry", "E_carry_inverso": "E · Carry inverso", "B_corto_alt_btc": "B · Corto altcoin vs BTC",
           "D_tendencia": "D · Tendencia BTC/ETH", "F_fin_de_semana": "F · Fin de semana (acciones)",
           "G_rafaga": "G · Ráfaga de momentum", "cartera": "Cartera"}


def num(x, dec=2):
    """1234.5 → '1.234,50' (formato español)."""
    try:
        s = f"{float(x):,.{dec}f}"
    except (TypeError, ValueError):
        return str(x)
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def precio(x):
    x = float(x)
    dec = 2 if x >= 100 else (4 if x >= 1 else (6 if x >= 0.01 else 8))
    return num(x, dec)


def cantidad(x):
    x = abs(float(x))
    return num(x, 2 if x >= 100 else (4 if x >= 1 else 6))


def base(sym):
    return sym.replace("USDT", "") if sym else ""


def _f(pat, text, cast=float):
    m = re.search(pat, text or "")
    if not m:
        return None
    try:
        return cast(m.group(1).replace(",", ""))
    except ValueError:
        return None


def euros(x):
    x = float(x)
    return f"{'+' if x > 0 else ('−' if x < 0 else '')}{num(abs(x))} $"


def formatear(mode, sleeve, event, symbol="", side="", qty="", price="", detail=""):
    head = f"{MODOS.get(mode, mode)} · BTC-lab"
    bl = BLOQUES.get(sleeve, sleeve)
    a = base(symbol)
    try:
        q, p = float(qty), float(price)
        notional = abs(q) * p
    except (TypeError, ValueError):
        q = p = notional = None

    if event == "arranque":
        cap = _f(r"capital ([\d,\.]+)", detail)
        bloques = re.findall(r"'([A-Z])_", detail)
        tg = "activos" if "Telegram activos" in detail else "no configurados"
        return (f"{head}\n▶️ Bot encendido\nCapital: {num(cap) if cap else '?'} $\nBloques activos: {', '.join(sorted(bloques)) or '?'}\n"
                f"Avisos de Telegram: {tg}")

    if event == "resumen":
        cap = _f(r"capital ([\d,\.]+)", detail); dd = _f(r"caída ([\d\.]+) %", detail)
        lines, n_ab, n_ce = [], 0, 0
        for name, bal, ab, ce in re.findall(r"(\w+): ([\d,\.]+) \| abiertas (\d+) \| cerradas (\d+)", detail):
            n_ab += int(ab); n_ce += int(ce)
            lines.append(f"• {BLOQUES.get(name, name)}: {num(bal.replace(',', ''))} $ · {ab} abierta(s)")
        extra = "\n⚠️ Hay símbolos bloqueados por descuadre (ver panel)." if "bloqueados" in detail else ""
        return (f"{head}\n📊 Resumen diario\nCapital: {num(cap) if cap else '?'} $ · caída desde el máximo: {num(dd or 0, 1)} %\n"
                f"Operaciones abiertas: {n_ab} · cerradas: {n_ce}\n\n" + "\n".join(lines) + extra)

    if event == "entrada" and q is not None:
        if sleeve == "B_corto_alt_btc":
            ratio, R = _f(r"ratio=([\d\.e\-\+]+)", detail), _f(r"R=([\d\.e\-\+]+)", detail)
            btc = _f(r"BTC ([\+\-]?[\d\.e\-]+)", detail)
            pb = _f(r"@ ([\d\.]+)", detail) or (notional / btc if btc else None)
            stop_pct = (R / ratio) if ratio and R else None
            riesgo = notional * stop_pct if stop_pct else None
            msg = f"{head}\n🔻 Nueva operación · {bl} (futuros)\nEntrada:\n• Corto en el futuro de {a}: {cantidad(q)} {a} a {precio(p)} $ (≈ {num(notional)} $)\n"
            if btc:
                msg += f"• Largo en el futuro de BTC: {cantidad(btc)} BTC a {precio(pb)} $ (≈ {num(abs(btc) * pb)} $) como cobertura\n"
            msg += f"Apuesta: {a} lo hará peor que BTC (si todo el mercado sube o baja, una pata compensa a la otra)\n"
            if riesgo:
                msg += (f"Stop: si {a} sube un {num(100 * stop_pct, 1)} % más que BTC. Si BTC no se mueve, equivale a {a} en "
                        f"≈ {precio(p * (1 + stop_pct))} $. Pérdida ≈ {num(riesgo)} $")
            return msg
        if sleeve == "D_tendencia":
            stop = _f(r"stop=([\d\.]+)", detail)
            loss = abs(q) * (p - stop) if stop else None
            return (f"{head}\n📈 Nueva operación · {bl} (futuros)\nEntrada: largo en el futuro de {a}, {cantidad(q)} {a} a {precio(p)} $ (≈ {num(notional)} $)\n"
                    + (f"Stop inicial: {precio(stop)} $ ({num(100 * (stop / p - 1), 1)} %) → pérdida máxima ≈ {num(loss)} $\n" if stop else "")
                    + "El stop sube solo a medida que sube el precio.")
        if sleeve in ("A_carry", "E_carry_inverso"):
            y = _f(r"rendimiento ([\d\.\-]+)%", detail)
            anual = f" (ahora ≈ {num(y * 3 * 365, 1)} % al año)" if y is not None else ""
            if sleeve == "A_carry":
                how = f"Compra {cantidad(q)} {a} en spot (moneda real) y abre un corto del mismo tamaño en el futuro (≈ {num(notional)} $ por pata)"
                why = "No apuesta por el precio: cobra lo que pagan los que compran con apalancamiento"
            else:
                how = f"Abre un largo de {cantidad(q)} {a} en el futuro y vende lo mismo en spot con monedas prestadas (≈ {num(notional)} $ por pata)"
                why = ("No apuesta por el precio (una pata compensa a la otra): cobra lo que pagan cada 8 h los que están en corto, "
                       "descontado el interés del préstamo")
            return f"{head}\n💵 Nueva operación · {bl}\n{how}\n{why}{anual}."
        if sleeve == "G_rafaga":
            stop = _f(r"stop=([\d\.e\-\+]+)", detail); r3 = _f(r"ret3=([\d\.\-]+)%", detail)
            loss = abs(q) * (p - stop) if stop else None
            return (f"{head}\n📈 Nueva operación · {bl} (futuros)\n"
                    f"Entrada: largo en el futuro de {a}, {cantidad(q)} {a} a {precio(p)} $ (≈ {num(notional)} $)\n"
                    + (f"Stop: {precio(stop)} $ ({num(100 * (stop / p - 1), 1)} %) → pérdida máxima ≈ {num(loss)} $\n" if stop else "")
                    + f"Motivo: {a} subió {num(r3 or 0, 1)} % en 3 h con un pico anormal de operaciones.\n"
                    "Se cierra si a las 6 h va en negativo, si toca el stop o como máximo a las 60 h.")
        if sleeve == "F_fin_de_semana":
            W = _f(r"W=([\+\-]?[\d\.]+)%", detail)
            verb = "Corto" if side == "SELL" else "Largo"
            return (f"{head}\n🔄 Nueva operación · {bl} (futuros)\n{verb} en el futuro de {a}: {cantidad(q)} a {precio(p)} $ (≈ {num(notional)} $)\n"
                    f"La acción se movió {num(W or 0, 2)} % durante el fin de semana con la bolsa cerrada; se apuesta a que "
                    f"devuelve parte al reabrir. Se cierra el lunes a las 03:00 UTC.")

    if event == "salida":
        pnl = _f(r"pnl=([\-\d\.]+)", detail)
        why = (detail or "").split(" pnl=")[0] if sleeve == "G_rafaga" else (
            (detail or "").split(" ")[0] if sleeve in ("A_carry", "E_carry_inverso", "B_corto_alt_btc") else "")
        motivos = {"stop": "saltó el stop", "stop_horario": "saltó el stop (comprobación horaria)",
                   "sin_datos": "la moneda dejó de tener datos (posible deslistado)", "rendimiento": "el funding dejó de compensar"}
        icon = "✅" if (pnl or 0) > 0 else "❌"
        fund = _f(r"funding=([\-\d\.]+)", detail)
        return (f"{head}\n{icon} Operación cerrada · {bl} · {a}\nResultado: {euros(pnl) if pnl is not None else '?'}"
                + (f" (de ello, funding cobrado: {euros(fund)})" if fund is not None else "")
                + (f"\nMotivo: {motivos.get(why, why)}" if why and not why.startswith("pnl") else ""))

    if event == "ampliacion" and q is not None:
        if sleeve == "B_corto_alt_btc":
            return (f"{head}\n➕ Amplía posición · {bl}\n{a} sigue debilitándose frente a BTC: amplía el corto en {cantidad(q)} {a} "
                    f"a {precio(p)} $ (con su cobertura en BTC).\n{detail}.\nTodo usa el mismo stop dinámico.")
        return (f"{head}\n➕ Amplía posición · {bl}\n{a} sigue subiendo: añade {cantidad(q)} {a} a {precio(p)} $.\n{detail}.\n"
                "Todo usa el mismo stop dinámico.")
    if event in ("error", "error_entrada"):
        return f"{head}\n⚠️ Error · {bl} {a}\n{detail}\nSi se repite varias horas seguidas, revisa el panel o el VPS."
    if event == "revisar":
        return f"{head}\n⚠️ La cartera cae {detail.replace('caída', '').strip()}. Es una alerta para revisar, el bot sigue funcionando."
    if event == "detenido":
        return f"{head}\n🛑 Bot detenido por caída ({detail}). No abrirá operaciones nuevas hasta que lo revises."
    if event == "descuadre":
        return (f"{head}\n⚠️ Descuadre con Binance en {a}: {detail}.\nEl bot no abrirá nada nuevo en {a} hasta revisarlo.")
    if event == "margen_transferido":
        return f"{head}\n🔁 {bl} · {a}: el bot ha movido fondos entre tus cuentas de Binance para mantener el margen."
    if event in ("reequilibrar_margen", "margen_insuficiente"):
        return f"{head}\n⚠️ {bl} · {a}: margen justo; el bot ha reducido la posición para evitar una liquidación. {detail}"
    if event == "sin_prestamo":
        return f"{head}\nℹ️ {bl} · {a}: Binance no presta esta moneda ahora; se omite la operación."
    return f"{head}\n{bl} · {event} {a} {side} {qty} {price} {detail}".strip()

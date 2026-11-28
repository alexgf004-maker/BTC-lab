"""Avisos de Telegram en español claro (el diario CSV sigue guardando el detalle técnico)."""
from __future__ import annotations

import re

MODOS = {"paper": "🧪 SIMULADO", "testnet": "🧪 PRUEBAS", "live": "💰 REAL"}
BLOQUES = {"A_carry": "A · Carry", "E_carry_inverso": "E · Carry inverso", "B_corto_alt_btc": "B · Corto altcoin vs BTC",
           "D_tendencia": "D · Tendencia BTC/ETH", "F_fin_de_semana": "F · Fin de semana (acciones)",
           "G_rafaga": "G · Ráfaga de momentum", "H_prima": "H · Prima rápida (EN PRUEBA)",
           "I_coinbase": "I · Prima de Coinbase (EN PRUEBA)", "J_redondos": "J · Ruptura falsa de redondos (EN PRUEBA)",
           "K_tokenizadas": "K · Arbitraje de tokenizadas (EN PRUEBA)",
           "L_doble_techo": "L · Doble techo (EN PRUEBA)", "M_B_filtrado": "M · B con filtro de funding (EN PRUEBA)",
           "cartera": "Cartera"}


LINEA = "━━━━━━━━━━━━━━"
EN_PRUEBA = {"H_prima", "I_coinbase", "J_redondos", "K_tokenizadas", "L_doble_techo", "M_B_filtrado"}


def pct(x):
    return f"{'+' if x > 0 else ('−' if x < 0 else '')}{num(abs(100 * x), 1)} %"


def dir_tag(d, a):
    return f"🟢 LARGO en {a} · gana si SUBE" if d > 0 else f"🔴 CORTO en {a} · gana si BAJA"


def tras(pos):
    """Texto técnico que se añade al cerrar una operación: dirección, precio y hora de entrada (para el aviso de cierre)."""
    px = next((pos[k] for k in ("px_alt", "perp_px", "entry") if isinstance(pos.get(k), (int, float))), None)
    t = str(pos.get("entry_time", "")).replace(" ", "T").replace("+00:00", "")
    if isinstance(pos.get("lado"), (int, float)):
        d = pos["lado"]
    elif isinstance(pos.get("side"), (int, float)):
        d = pos["side"]
    elif "qty_alt" in pos:
        d = -1
    else:
        q = pos.get("qty")
        d = (1 if q > 0 else -1) if isinstance(q, (int, float)) and q else 0
    lado = {1: "largo", -1: "corto"}.get(int(d) if d else 0, "")
    return (f" entrada={px:.10g}" if px else "") + (f" desde={t}" if t else "") + (f" lado={lado}" if lado else "")


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


def formatear(mode, sleeve, event, symbol="", side="", qty="", price="", detail="", ts=None):
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
        prueba = sleeve in EN_PRUEBA
        top = f"{head}\n📥 NUEVA OPERACIÓN{' · 🧪 EN PRUEBA' if prueba else ''}\n{bl.replace(' (EN PRUEBA)', '')}\n{LINEA}\n"
        pie = "\n🧪 Simulada aparte: no cuenta en tu capital." if prueba else ""
        if sleeve in ("B_corto_alt_btc", "M_B_filtrado"):
            ratio, R = _f(r"ratio=([\d\.e\-\+]+)", detail), _f(r"R=([\d\.e\-\+]+)", detail)
            btc = _f(r"BTC ([\+\-]?[\d\.e\-]+)", detail)
            pb = _f(r"@ ([\d\.]+)", detail) or (notional / btc if btc else None)
            stop_pct = (R / ratio) if ratio and R else None
            riesgo = notional * stop_pct if stop_pct else None
            msg = (top + f"🔴 CORTO en {a}  +  🟢 LARGO en BTC (cobertura)\nGana si {a} lo hace PEOR que BTC\n{LINEA}\n"
                   f"🔴 Corto en el futuro de {a}: {cantidad(q)} {a} a {precio(p)} $ (≈ {num(notional)} $)\n")
            if btc:
                msg += f"🟢 Largo en el futuro de BTC: {cantidad(btc)} BTC a {precio(pb)} $ (≈ {num(abs(btc) * pb)} $)\n"
            if riesgo:
                msg += (f"🛑 Stop: si {a} sube un {num(100 * stop_pct, 1)} % más que BTC (con BTC quieto, {a} en "
                        f"≈ {precio(p * (1 + stop_pct))} $) → pérdida ≈ {num(riesgo)} $\n")
            return msg + "💡 Si todo el mercado sube o baja, una pata compensa a la otra. El stop baja solo si la apuesta va bien."
        if sleeve in ("A_carry", "E_carry_inverso", "H_prima", "K_tokenizadas"):
            if sleeve == "A_carry":
                y = _f(r"rendimiento ([\d\.\-]+)%", detail)
                how = f"🟢 Compra {cantidad(q)} {a} en spot  +  🔴 corto igual en el futuro (≈ {num(notional)} $ por pata)"
                why = "Cobra el funding que pagan los que compran con apalancamiento" + (f" (ahora ≈ {num(y * 3 * 365, 1)} % al año)" if y is not None else "")
            elif sleeve == "E_carry_inverso":
                y = _f(r"rendimiento ([\d\.\-]+)%", detail)
                how = f"🟢 Largo de {cantidad(q)} {a} en el futuro  +  🔴 venta igual en spot con monedas prestadas (≈ {num(notional)} $ por pata)"
                why = ("Cobra el funding que pagan los cortos, menos el interés del préstamo"
                       + (f" (ahora ≈ {num(y * 3 * 365, 1)} % al año)" if y is not None else ""))
            elif sleeve == "H_prima":
                pr = _f(r"prima=([\-\d\.]+)%", detail)
                how = f"🟢 Largo en el futuro de {a} a {precio(p)} $  +  🔴 venta igual en spot (≈ {num(notional)} $ por pata)"
                why = (f"El futuro cotiza un {num(abs(pr or 0), 2)} % por debajo del spot; gana cuando la diferencia se cierra "
                       "(menos de 0,1 % o como máximo 24 h)")
            else:
                return (top + f"⚪ NEUTRAL · arbitraje entre el token spot y el futuro de {a}\nNo apuesta a la dirección del precio\n{LINEA}\n"
                        f"💡 {detail}" + pie)
            return top + f"⚪ NEUTRAL · no apuesta a la dirección del precio\n{LINEA}\n{how}\n💡 {why}." + pie
        d = 1 if side == "BUY" else -1
        msg = top + dir_tag(d, a) + f"\n{LINEA}\n💵 Entrada: {precio(p)} $\n📦 Tamaño: {cantidad(q)} {a} (≈ {num(notional)} $)\n"
        stop = _f(r"stop=([\d\.e\-\+]+)", detail)
        if stop:
            loss = abs(q) * abs(p - stop)
            msg += f"🛑 Stop: {precio(stop)} $ ({pct(stop / p - 1)}) → pérdida máx. ≈ {num(loss)} $\n"
        if sleeve == "D_tendencia":
            return msg + "🚪 Salida: sin objetivo fijo; el stop sube solo a medida que sube el precio.\n💡 Por qué: rompió su máximo de 20 días con tendencia alcista."
        if sleeve == "G_rafaga":
            r3 = _f(r"ret3=([\d\.\-]+)%", detail)
            return (msg + "🚪 Salida: si a las 6 h va en negativo, si toca el stop o como máximo a las 60 h.\n"
                    f"💡 Por qué: subió {num(r3 or 0, 1)} % en 3 h con un pico anormal de operaciones.")
        if sleeve == "F_fin_de_semana":
            W = _f(r"W=([\+\-]?[\d\.]+)%", detail)
            return (msg + "🚪 Salida: el lunes a las 03:00 UTC.\n"
                    f"💡 Por qué: la acción se movió {num(W or 0, 2)} % el fin de semana con la bolsa cerrada; se apuesta a que devuelve parte.")
        if sleeve in ("I_coinbase", "J_redondos", "L_doble_techo"):
            extra = "\n".join(x for x in (detail or "").split("\n")[1:] if x.strip()) or detail
            extra = re.sub(r"\s*stop=\S+", "", extra)
            return msg + f"💡 {extra}" + pie
        return msg + (f"💡 {detail}" if detail else "") + pie

    if event == "salida":
        pnl = _f(r"pnl=([\-\d\.]+)", detail)
        why = (detail or "").split(" pnl=")[0] if sleeve in ("G_rafaga", "H_prima", "I_coinbase", "J_redondos", "K_tokenizadas", "L_doble_techo") else (
            (detail or "").split(" ")[0] if sleeve in ("A_carry", "E_carry_inverso", "B_corto_alt_btc", "M_B_filtrado") else "")
        motivos = {"stop": "saltó el stop", "stop_horario": "saltó el stop (comprobación horaria)",
                   "sin_datos": "la moneda dejó de tener datos (posible deslistado)", "rendimiento": "el funding dejó de compensar"}
        gana = (pnl or 0) > 0
        title = "✅ CERRADA CON GANANCIA" if gana else "❌ CERRADA CON PÉRDIDA"
        prueba = " · 🧪 EN PRUEBA" if sleeve in EN_PRUEBA else ""
        lado = _f(r"lado=(\w+)", detail, str)
        if sleeve in ("A_carry", "E_carry_inverso", "H_prima", "K_tokenizadas"):
            dl = "⚪ Era NEUTRAL (no apostaba a la dirección)"
        elif sleeve in ("B_corto_alt_btc", "M_B_filtrado"):
            dl = f"🔴 Era CORTO en {a} contra BTC (ganaba si {a} lo hacía peor que BTC)"
        elif lado == "largo":
            dl = "🟢 Era LARGO (ganaba si subía)"
        elif lado == "corto":
            dl = "🔴 Era CORTO (ganaba si bajaba)"
        else:
            dl = ""
        fund = _f(r"funding=([\-\d\.]+)", detail)
        msg = (f"{head}\n{title}{prueba}\n{bl.replace(' (EN PRUEBA)', '')} · {a}\n{LINEA}\n" + (dl + "\n" if dl else "")
               + f"💰 Resultado: {euros(pnl) if pnl is not None else '?'}" + (f" (funding: {euros(fund)})" if fund is not None else "")
               + f"\n{LINEA}")
        e_px = _f(r"entrada=([\d\.eE\+\-]+)", detail)
        m_t = re.search(r"desde=(\S+)", detail or "")
        if m_t:
            try:
                import pandas as _pd
                t0 = _pd.Timestamp(m_t.group(1).replace("T", " ")[:19])
                t1 = _pd.Timestamp(str(ts).replace("T", " ")[:19]) if ts else None
                neutral = dl.startswith("⚪")
                msg += f"\n📥 Entró: {t0:%d/%m %H:%M} UTC" + (f" a {precio(e_px)} $" if e_px and not neutral else "")
                if t1 is not None:
                    mov = f" ({pct(p / e_px - 1)})" if e_px and p and not neutral else ""
                    msg += f"\n📤 Salió: {t1:%d/%m %H:%M} UTC" + (f" a {precio(p)} ${mov}" if p and not neutral else "")
                    hrs = (t1 - t0).total_seconds() / 3600
                    if hrs >= 0:
                        msg += f"\n⏱ Duró {num(hrs, 0)} h" if hrs < 48 else f"\n⏱ Duró {num(hrs / 24, 1)} días"
            except Exception:
                pass
        if why and not why.startswith("pnl"):
            msg += f"\n📝 Motivo: {motivos.get(why, why)}"
        return msg

    if event == "ampliacion" and q is not None:
        if sleeve in ("B_corto_alt_btc", "M_B_filtrado"):
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

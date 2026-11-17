"""Avisos por Telegram (opcionales). Configuración por variables de entorno: TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID.
Si no están definidas, los avisos solo quedan en el diario y en el log. Un fallo al avisar nunca detiene el bot."""
from __future__ import annotations

import logging
import os
import time

import requests

log = logging.getLogger("bot.notify")

IMPORTANT = {"entrada", "salida", "error", "error_entrada", "reequilibrar_margen", "margen_transferido", "margen_insuficiente",
             "detenido", "revisar", "descuadre", "sin_prestamo", "arranque", "resumen"}


class Telegram:
    def __init__(self, token=None, chat_id=None, prefix="BTC-lab"):
        self.token = token if token is not None else os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat = chat_id if chat_id is not None else os.environ.get("TELEGRAM_CHAT_ID", "")
        self.prefix, self._last = prefix, 0.0
        self.sent = []                                    # para pruebas
        self.important = IMPORTANT

    @property
    def enabled(self):
        return bool(self.token and self.chat)

    def send(self, text):
        msg = f"[{self.prefix}] {text}"[:4000]
        self.sent.append(msg)
        if not self.enabled:
            return False
        wait = 1.1 - (time.time() - self._last)           # Telegram admite ~1 mensaje por segundo por chat
        if wait > 0:
            time.sleep(wait)
        try:
            r = requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage",
                              data={"chat_id": self.chat, "text": msg, "disable_web_page_preview": "true"}, timeout=10)
            self._last = time.time()
            return r.ok
        except requests.RequestException as e:
            log.warning("no se pudo enviar el aviso: %s", e)
            return False

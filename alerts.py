# -*- coding: utf-8 -*-
"""
Alerte catre familie (Sprint 4) — cand Scam-Shield semnaleaza un pericol.

PRINCIPIUL GDPR CENTRAL — MINIMIZAREA DATELOR:
Alerta NU trimite continutul conversatiei. Trimite doar: tipul evenimentului,
ora, si categoria de risc (ex. "autoritate_falsa"). Familia primeste un
ÎNDEMN sa verifice, nu o transcriere. Detaliile raman in panoul de familie,
accesibil doar cu PIN si doar cu consimtamant (vezi app.py).

De ce e legitim fara consimtamant separat pentru continut: alerta e o masura
de PROTECTIE (interesul vital al persoanei, escrocherie in curs), si e
configurata la instalare de familie impreuna cu varstnicul. Trimite minimul
necesar pentru a proteja — nimic peste.

Canale (toate optionale, configurate prin mediu):
- email (SMTP) · webhook (POST JSON, ex. catre un bot) · log (mereu activ)
Fail-safe: un canal cazut NU blocheaza celelalte si NU arunca eroarea in
fluxul de chat (protectia utilizatorului e prioritara fata de livrarea alertei).
"""
from __future__ import annotations

import json
import smtplib
import time
import urllib.request
from dataclasses import dataclass, field
from email.mime.text import MIMEText


@dataclass
class AlertEvent:
    kind: str                    # ex. "scam_likely"
    at: str                      # timestamp lizibil
    category: str = ""           # categoria scam, ex. "autoritate_falsa"
    lang: str = "ro"

    def summary(self) -> str:
        cat = f" ({self.category})" if self.category else ""
        if self.lang == "en":
            return (f"AmiDor safety alert: a possible scam was detected at "
                    f"{self.at}{cat}. Please check in with your relative. "
                    f"(No conversation content is shared.)")
        return (f"Alertă AmiDor: o posibilă înșelăciune a fost detectată la "
                f"{self.at}{cat}. Sunați-vă, vă rog, ruda. "
                f"(Conținutul conversației NU este trimis.)")


# ------------------------------------------------------------------ canale
@dataclass
class LogChannel:
    path: str
    name: str = "log"

    def send(self, ev: AlertEvent) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"kind": ev.kind, "at": ev.at,
                                "category": ev.category}, ensure_ascii=False) + "\n")


@dataclass
class EmailChannel:
    host: str; port: int; user: str; password: str
    to_addr: str; from_addr: str = ""
    name: str = "email"

    def send(self, ev: AlertEvent) -> None:
        msg = MIMEText(ev.summary(), _charset="utf-8")
        msg["Subject"] = "AmiDor — alertă de siguranță" if ev.lang != "en" else "AmiDor — safety alert"
        msg["From"] = self.from_addr or self.user
        msg["To"] = self.to_addr
        with smtplib.SMTP(self.host, self.port, timeout=15) as s:
            s.starttls()
            s.login(self.user, self.password)
            s.send_message(msg)


@dataclass
class WebhookChannel:
    url: str
    name: str = "webhook"

    def send(self, ev: AlertEvent) -> None:
        body = json.dumps({"kind": ev.kind, "at": ev.at,
                           "category": ev.category, "text": ev.summary()}).encode()
        req = urllib.request.Request(self.url, data=body,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15).read()


@dataclass
class CallableChannel:
    """Canal din orice functie (ev)->None. Pentru teste si integrari custom."""
    fn: object
    name: str = "callable"

    def send(self, ev: AlertEvent) -> None:
        self.fn(ev)


# ------------------------------------------------------------------ manager
class AlertManager:
    """Dispecerizeaza catre toate canalele, cu de-duplicare (nu spam familia):
    o alerta de aceeasi categorie e trimisa cel mult o data la `cooldown` sec."""

    def __init__(self, channels: list, cooldown: float = 300.0):
        self.channels = channels
        self.cooldown = cooldown
        self._last: dict[str, float] = {}
        self.errors: list[str] = []

    def _throttled(self, ev: AlertEvent) -> bool:
        key = f"{ev.kind}:{ev.category}"
        now = time.time()
        if now - self._last.get(key, 0) < self.cooldown:
            return True
        self._last[key] = now
        return False

    def dispatch(self, ev: AlertEvent) -> dict:
        if not self.channels:
            return {"sent": 0, "throttled": False, "reason": "no channels"}
        if self._throttled(ev):
            return {"sent": 0, "throttled": True}
        sent = 0
        for ch in self.channels:
            try:
                ch.send(ev)
                sent += 1
            except Exception as e:           # un canal cazut nu blocheaza restul
                self.errors.append(f"{getattr(ch, 'name', '?')}: {e}")
        return {"sent": sent, "throttled": False, "channels": len(self.channels)}


def build_from_env(os_environ, log_path: str) -> AlertManager:
    """Construieste managerul din variabile de mediu. Log-ul e mereu prezent."""
    channels: list = [LogChannel(log_path)]
    to = os_environ.get("ALERT_EMAIL_TO")
    host = os_environ.get("ALERT_SMTP_HOST")
    if to and host:
        channels.append(EmailChannel(
            host=host, port=int(os_environ.get("ALERT_SMTP_PORT", "587")),
            user=os_environ.get("ALERT_SMTP_USER", ""),
            password=os_environ.get("ALERT_SMTP_PASS", ""),
            to_addr=to, from_addr=os_environ.get("ALERT_EMAIL_FROM", "")))
    hook = os_environ.get("ALERT_WEBHOOK_URL")
    if hook:
        channels.append(WebhookChannel(hook))
    cooldown = float(os_environ.get("ALERT_COOLDOWN", "300"))
    return AlertManager(channels, cooldown=cooldown)

# -*- coding: utf-8 -*-
"""
Scam-Shield v0 — detector de tipare de escrocherie tipice pentru varstnici.
DIFERENTIATORUL AmiDor: nimeni din piata companion nu ofera protectie activa.

STATUS ONEST (ca peste tot in ecosistem): v0, euristica de tipare RO/EN, NU
o garantie. Escrocii inoveaza; lista NU e exhaustiva. Directia de esec e cea
sigura: la orice semnal, AmiDor NU actioneaza in locul omului si NU da sfaturi
tranzactionale — intrerupe si indeamna sa sune un om de incredere. Fals-pozitiv
(o alarma cand nu e cazul) = neplacut dar sigur. Fals-negativ e riscul real,
de aceea pragul e jos si mesajul e mereu "verifica cu familia", nu "e in regula".

Ce prinde v0 (cele mai frecvente scenarii raportate la varstnici):
- ruda in criza / "nepotul la spital, trimite bani acum"
- autoritate falsa (banca/politie/ANAF) care cere date/parole/coduri
- urgenta + secret ("nu spune nimanui", "chiar acum")
- cerere de cod OTP / card / transfer / crypto / carduri cadou
- premii/mosteniri neasteptate care cer o plata in avans
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum


class ScamRisk(Enum):
    NONE = "none"
    POSSIBLE = "possible"   # un singur semnal slab - flag bland, conversatia continua
    LIKELY = "likely"       # semnal(e) tare - intrerupe si indeamna la verificare umana


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


# Categorii de semnale. Fiecare pattern e ilustrativ, nu exhaustiv.
_STRONG = {
    "cod_otp_card": [
        r"\bcod(ul)?\b.{0,20}\b(sms|otp|card|banca|verificare|autentificare)\b",
        r"\bcvv\b", r"\bpin(ul)?\b.{0,15}\bcard",
        r"\bnumar(ul)?\b.{0,10}\bcard",
        r"\bone[- ]?time\b", r"\bverification code\b", r"\bcard number\b",
    ],
    "transfer_bani": [
        r"\btrimite\b.{0,25}\b(bani|suma|lei|euro|transfer)\b",
        r"\btransfer(a|ati)?\b.{0,20}\b(urgent|acum|imediat)\b",
        r"\brevolut\b|\bwestern union\b|\bmoneygram\b",
        r"\b(crypto|bitcoin|cont)\b.{0,20}\b(transfer|trimite|depune)\b",
        r"\bcard(uri)? cadou\b|\bgift card", r"\bsend\b.{0,20}\bmoney\b",
    ],
    "autoritate_falsa": [
        r"\b(sunt|aici|din partea)\b.{0,25}\b(banca|bank|politie|police|anaf|primaria|microsoft|amazon)\b",
        r"\b(agent|inspector|ofiter|reprezentant)\b.{0,20}\b(banca|politie|fisc|securitate)\b",
        r"\bcontul (tau|dvs).{0,20}\b(blocat|compromis|suspendat|piratat)\b",
        r"\byour account\b.{0,15}\b(blocked|suspended|compromised)\b",
    ],
    "ruda_criza": [
        r"\b(nepot|nepotul|fiul|fiica|copilul)\b.{0,30}\b(accident|spital|arestat|inchisoare|probleme|urgent)\b",
        r"\bam avut un accident\b.{0,30}\b(bani|trimite|urgent)\b",
        r"\bgrandson\b.{0,30}\b(hospital|accident|jail|money)\b",
    ],
}
_WEAK = {
    # urgenta si secret sunt semnale SEPARATE: impreuna = tiparul clasic -> LIKELY
    "urgenta": [
        r"\b(chiar )?acum\b.{0,15}\b(imediat|urgent|repede)\b",
        r"\bimediat\b|\burgent\b", r"\bin urmatoarele (\d+ )?(minute|ore)\b",
        r"\bnow\b.{0,12}\b(immediately|urgent|quickly)\b",
    ],
    "secret": [
        r"\bnu spune(ti)? nimanui\b", r"\bpastreaza secret\b|\bsa ramana intre noi\b",
        r"\bdo(n'?t| not) tell anyone\b", r"\bkeep (it|this) secret\b",
    ],
    "premiu_neasteptat": [
        r"\bai castigat\b|\bfelicitari\b.{0,20}\bcastig",
        r"\bmostenire\b.{0,25}\b(neasteptata|strain|taxa)\b",
        r"\byou('?ve)? won\b|\binheritance\b.{0,20}\bfee\b",
    ],
}


def _compile(groups):
    return {cat: re.compile("|".join(pats), re.IGNORECASE)
            for cat, pats in groups.items()}


_STRONG_RE = _compile(_STRONG)
_WEAK_RE = _compile(_WEAK)


@dataclass
class ScamSignal:
    risk: ScamRisk
    categories: list
    is_heuristic_v0: bool = True


def detect_scam(text: str) -> ScamSignal:
    """Un semnal TARE -> LIKELY. Doua semnale slabe -> LIKELY (urgenta+secret e
    tiparul clasic). Un singur semnal slab -> POSSIBLE."""
    t = _norm(text)
    strong = [c for c, rx in _STRONG_RE.items() if rx.search(t)]
    weak = [c for c, rx in _WEAK_RE.items() if rx.search(t)]

    if strong or len(weak) >= 2:
        return ScamSignal(ScamRisk.LIKELY, strong + weak)
    if weak:
        return ScamSignal(ScamRisk.POSSIBLE, weak)
    return ScamSignal(ScamRisk.NONE, [])


SCAM_INTERRUPT = (
    "Stai puțin — ce-mi descrii seamănă cu o încercare de înșelăciune, iar eu "
    "țin la tine. Nimeni de la o bancă, poliție sau instituție nu cere prin "
    "telefon coduri, parole sau bani trimiși urgent. **Nu da niciun cod și nu "
    "trimite bani.** Închide, respiră, și sună chiar acum o persoană de "
    "încredere — un copil, un vecin. Dacă vrei, te ajut să-i suni."
)


def scam_response(signal: ScamSignal) -> dict | None:
    if signal.risk == ScamRisk.LIKELY:
        return {
            "action": "interrupt_and_warn",
            "risk": signal.risk.value,
            "categories": signal.categories,
            "message": SCAM_INTERRUPT,
            "flag_family": True,
            "continue_flow": False,
        }
    if signal.risk == ScamRisk.POSSIBLE:
        return {
            "action": "gentle_caution",
            "risk": signal.risk.value,
            "categories": signal.categories,
            "message": None,      # nu intrerupem; doar flag catre familie
            "flag_family": True,
            "continue_flow": True,
        }
    return None

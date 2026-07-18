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
        # FR
        r"\bcode\b.{0,20}\b(sms|otp|carte|banque|v[ée]rification)\b",
        r"\bnum[ée]ro de carte\b",
        # DE
        r"\bcode\b.{0,20}\b(sms|otp|karte|bank|verifizierung)\b",
        r"\bkartennummer\b",
        # IT
        r"\bcodice\b.{0,20}\b(sms|otp|carta|banca|verifica)\b",
        r"\bnumero (?:di |della )?carta\b",
        # ES
        r"\bc[oó]digo\b.{0,20}\b(sms|otp|tarjeta|banco|verificaci[oó]n)\b",
        r"\bn[uú]mero de tarjeta\b",
    ],
    "transfer_bani": [
        r"\btrimite\b.{0,25}\b(bani|suma|lei|euro|transfer)\b",
        r"\btransfer(a|ati)?\b.{0,20}\b(urgent|acum|imediat)\b",
        r"\brevolut\b|\bwestern union\b|\bmoneygram\b",
        r"\b(crypto|bitcoin|cont)\b.{0,20}\b(transfer|trimite|depune)\b",
        r"\bcard(uri)? cadou\b|\bgift card", r"\bsend\b.{0,20}\bmoney\b",
        # FR
        r"\benvoy(er|ez)\b.{0,25}\b(argent|somme|euros?|virement)\b",
        r"\bvirement\b.{0,20}\b(urgent|imm[ée]diat|maintenant)\b",
        # DE
        r"\b[uü]berweisen\b.{0,25}\b(geld|betrag|euro|sofort)\b",
        r"\b[uü]berweisung\b.{0,20}\b(dringend|sofort|jetzt)\b",
        # IT
        r"\binvi(are|a)\b.{0,25}\b(soldi|denaro|euro|bonifico)\b",
        r"\bbonifico\b.{0,20}\b(urgente|subito|immediatamente)\b",
        # ES
        r"\benvi(ar|e)\b.{0,25}\b(dinero|suma|euros?|transferencia)\b",
        r"\btransferencia\b.{0,20}\b(urgente|ahora|inmediatamente)\b",
    ],
    "autoritate_falsa": [
        r"\b(sunt|aici|din partea)\b.{0,25}\b(banca|bank|politie|police|anaf|primaria|microsoft|amazon)\b",
        r"\b(agent|inspector|ofiter|reprezentant)\b.{0,20}\b(banca|politie|fisc|securitate)\b",
        r"\bcontul (tau|dvs).{0,20}\b(blocat|compromis|suspendat|piratat)\b",
        r"\byour account\b.{0,15}\b(blocked|suspended|compromised)\b",
        # FR
        r"\b(je suis|ici|de la part)\b.{0,25}\b(banque|police|imp[oô]ts|gendarmerie|microsoft|amazon)\b",
        r"\bvotre compte\b.{0,15}\b(bloqu[ée]|compromis|suspendu|pirat[ée])\b",
        # DE
        r"\b(ich bin|hier ist|im auftrag)\b.{0,25}\b(bank|polizei|finanzamt|microsoft|amazon)\b",
        r"\bihr konto\b.{0,15}\b(gesperrt|kompromittiert|gehackt)\b",
        # IT
        r"\b(sono|qui|da parte)\b.{0,25}\b(banca|polizia|agenzia entrate|microsoft|amazon)\b",
        r"\bil (?:suo|vostro) conto\b.{0,15}\b(bloccato|compromesso|sospeso)\b",
        # ES
        r"\b(soy|aqu[ií]|de parte)\b.{0,25}\b(banco|polic[ií]a|hacienda|microsoft|amazon)\b",
        r"\bsu cuenta\b.{0,15}\b(bloqueada|comprometida|suspendida)\b",
    ],
    "ruda_criza": [
        r"\b(nepot|nepotul|fiul|fiica|copilul)\b.{0,30}\b(accident|spital|arestat|inchisoare|probleme|urgent)\b",
        r"\bam avut un accident\b.{0,30}\b(bani|trimite|urgent)\b",
        r"\bgrandson\b.{0,30}\b(hospital|accident|jail|money)\b",
        # FR
        r"\b(petit-fils|fils|fille|enfant)\b.{0,30}\b(accident|h[oô]pital|arr[êe]t[ée]|prison|urgence)\b",
        # DE
        r"\b(enkel|sohn|tochter|kind)\b.{0,30}\b(unfall|krankenhaus|verhaftet|gef[aä]ngnis|dringend)\b",
        # IT
        r"\b(nipote|figlio|figlia|bambino)\b.{0,30}\b(incidente|ospedale|arrestat[oa]|prigione|urgente)\b",
        # ES
        r"\b(nieto|hijo|hija|ni[ñn]o)\b.{0,30}\b(accidente|hospital|arrestado|c[aá]rcel|urgente)\b",
    ],
}
_WEAK = {
    "urgenta": [
        r"\b(chiar )?acum\b.{0,15}\b(imediat|urgent|repede)\b",
        r"\bimediat\b|\burgent\b", r"\bin urmatoarele (\d+ )?(minute|ore)\b",
        r"\bnow\b.{0,12}\b(immediately|urgent|quickly)\b",
        # FR
        r"\bimm[ée]diatement\b|\burgent\b|\btout de suite\b",
        r"\bdans les prochaines (\d+ )?(minutes|heures)\b",
        # DE
        r"\bsofort\b|\bdringend\b|\bunverz[uü]glich\b",
        r"\bin den n[aä]chsten (\d+ )?(minuten|stunden)\b",
        # IT
        r"\bimmediatamente\b|\burgente\b|\bsubito\b",
        r"\bnei prossimi (\d+ )?(minuti|ore)\b",
        # ES
        r"\binmediatamente\b|\burgente\b|\bahora mismo\b",
        r"\ben los pr[oó]ximos (\d+ )?(minutos|horas)\b",
    ],
    "secret": [
        r"\bnu spune(ti)? nimanui\b", r"\bpastreaza secret\b|\bsa ramana intre noi\b",
        r"\bdo(n'?t| not) tell anyone\b", r"\bkeep (it|this) secret\b",
        # FR
        r"\bne (?:dites?|parlez?) [àa] personne\b", r"\bgardez (?:le |cela )?secret\b",
        r"\bentre nous\b|\bconfidentiel\b",
        # DE
        r"\bsagen sie niemandem\b|\berz[aä]hl(?:e|en sie) (?:es )?niemandem\b",
        r"\bgeheim halten\b|\bvertraulich\b",
        # IT
        r"\bnon (?:dire|dica) a nessuno\b", r"\btenga(?:lo)? segreto\b",
        r"\btra (?:noi|di noi)\b|\briservato\b",
        # ES
        r"\bno (?:le )?(?:digas?|cuentes?) a nadie\b", r"\bmant[ée]n(?:galo|lo) en secreto\b",
        r"\bentre nosotros\b|\bconfidencial\b",
    ],
    "premiu_neasteptat": [
        r"\bai castigat\b|\bfelicitari\b.{0,20}\bcastig",
        r"\bmostenire\b.{0,25}\b(neasteptata|strain|taxa)\b",
        r"\byou('?ve)? won\b|\binheritance\b.{0,20}\bfee\b",
        # FR
        r"\bvous avez gagn[ée]\b|\bf[ée]licitations\b.{0,20}\bgagn",
        r"\bh[ée]ritage\b.{0,25}\b(inattendu|frais|taxe)\b",
        # DE
        r"\bsie haben gewonnen\b|\bherzlichen gl[uü]ckwunsch\b.{0,20}\bgewinn",
        r"\berbschaft\b.{0,25}\b(unerwartet|geb[uü]hr|steuer)\b",
        # IT
        r"\bhai vinto\b|\bcongratulazioni\b.{0,20}\bvint",
        r"\beredit[àa]\b.{0,25}\b(inaspettat[oa]|tassa|costo)\b",
        # ES
        r"\bhas ganado\b|\bfelicidades\b.{0,20}\bganad",
        r"\bherencia\b.{0,25}\b(inesperada|tarifa|impuesto)\b",
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

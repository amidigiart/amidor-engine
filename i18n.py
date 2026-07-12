# -*- coding: utf-8 -*-
"""
i18n — cataloage de mesaje pentru AmiDor, de la inceput (Sprint 3).

De ce de la inceput: piata AmiDor e diaspora (parinti in RO, copii in DE/IT/
ES/FR) + varstnici din toata UE. Fiecare text livrat utilizatorului trece
prin acest catalog. Detectia de escrocherie (scam_shield) e independenta de
limba — patternurile acopera RO+EN; MESAJUL de raspuns vine de aici.

Structura: LOCALE -> chei. O limba noua = un dict nou; testul de completitudine
(test_i18n.py) refuza un catalog caruia ii lipseste orice cheie.

`speech` = codul BCP-47 pentru voce (STT/TTS), separat de codul de UI.
"""
from __future__ import annotations

_KEYS = {
    "lang_name", "speech", "greeting", "system_prompt", "ask_directive",
    "scam_interrupt", "honest_disagreement", "numeric_hint",
    "reanchor_reply", "uncorroborated_tag", "degraded_reply",
    "not_medical", "voice_privacy_notice",
}

CATALOG: dict[str, dict[str, str]] = {
    "ro": {
        "lang_name": "Română",
        "speech": "ro-RO",
        "greeting": ("Bună ziua! Sunt AmiDor, prietenul dumneavoastră digital. "
                     "Sunt aici să vă țin companie și să vă ajut cu ce pot. "
                     "Cum vă simțiți astăzi?"),
        "system_prompt": (
            "Ești AmiDor, un asistent digital cald și răbdător, care ține "
            "companie unei persoane în vârstă și vorbește în limba română. "
            "Ești un program de calculator, nu un om, și spui asta clar dacă "
            "ești întrebat; la o conversație nouă te prezinți: «Sunt AmiDor, "
            "prietenul tău digital». Vorbești simplu, cald, fără grabă, în "
            "fraze scurte, fără termeni tehnici. Nu ești medic și nu dai "
            "sfaturi medicale: la subiecte de sănătate sau medicamente, "
            "îndrumi blând spre medic sau farmacist. Nu ceri și nu accepți "
            "parole, coduri sau numere de card. Dacă nu ești sigur, spui "
            "sincer «nu știu, hai să verificăm» — mai bine decât să inventezi. "
            "Închei des cu o întrebare scurtă și caldă."),
        "scam_interrupt": (
            "Stai puțin — ce-mi descrii seamănă cu o încercare de înșelăciune, "
            "iar eu țin la tine. Nimeni de la o bancă, poliție sau instituție "
            "nu cere prin telefon coduri, parole sau bani trimiși urgent. "
            "**Nu da niciun cod și nu trimite bani.** Închide, respiră, și sună "
            "chiar acum o persoană de încredere — un copil, un vecin."),
        "honest_disagreement": (
            "Nu pot să-ți dau un răspuns sigur aici — sursele mele interne nu "
            "spun același lucru, iar decât să ghicesc, prefer să fiu sincer. "
            "{hint}Putem reformula întrebarea, sau o verificăm împreună cu "
            "cineva de încredere."),
        "numeric_hint": "Diferența e la cifre — iar la cifre nu am voie să aproximez. ",
        "reanchor_reply": ("Hai să ne oprim o clipă și să ne asigurăm că suntem "
                           "în pas: am înțeles bine ce mă întrebi? Spune-mi cu "
                           "alte cuvinte, te rog."),
        "uncorroborated_tag": ("\n\n(Notă: acest răspuns vine de la o singură "
                               "sursă și nu a putut fi verificat încrucișat acum.)"),
        "degraded_reply": ("Am o mică problemă tehnică chiar acum și nu vreau să "
                           "improvizez. Încearcă, te rog, puțin mai târziu."),
        "not_medical": "nu sunt medic și nu dau sfaturi medicale",
        "voice_privacy_notice": ("Vocea prin browser poate trimite ce spuneți "
                                 "către serviciile Google/Apple. Pentru "
                                 "confidențialitate deplină, folosiți vocea "
                                 "locală (server propriu)."),
        "ask_directive": (
            " REGULĂ ACTIVĂ (coerența conversației a scăzut): nu introduce "
            "informații noi. Reformulează pe scurt ce a spus persoana și pune "
            "o singură întrebare de clarificare, caldă."),
    },
    "en": {
        "lang_name": "English",
        "speech": "en-GB",
        "greeting": ("Hello! I'm AmiDor, your digital friend. I'm here to keep "
                     "you company and help where I can. How are you feeling today?"),
        "system_prompt": (
            "You are AmiDor, a warm and patient digital companion for an older "
            "adult, speaking English. You are a computer program, not a human, "
            "and you say so clearly if asked; at a new conversation you "
            "introduce yourself: 'I'm AmiDor, your digital friend'. You speak "
            "simply, warmly, unhurried, in short sentences, without jargon. You "
            "are not a doctor and give no medical advice: for health or "
            "medication, gently point to a doctor or pharmacist. You never ask "
            "for or accept passwords, codes or card numbers. If unsure, you say "
            "honestly 'I don't know, let's check' — better than inventing. You "
            "often close with a short, warm question."),
        "scam_interrupt": (
            "Hold on — what you're describing looks like a scam attempt, and I "
            "care about you. No real bank, police or institution asks for codes, "
            "passwords or urgent money transfers over the phone. **Don't give "
            "any code and don't send money.** Hang up, take a breath, and call "
            "someone you trust right now — a child, a neighbour."),
        "honest_disagreement": (
            "I can't give you a sure answer here — my internal sources don't "
            "agree, and rather than guess, I'd rather be honest. {hint}We can "
            "rephrase the question, or check it together with someone you trust."),
        "numeric_hint": "The difference is in the numbers — and with numbers I must not approximate. ",
        "reanchor_reply": ("Let's pause a moment to make sure we're in step: did "
                           "I understand your question right? Tell me in other "
                           "words, please."),
        "uncorroborated_tag": ("\n\n(Note: this answer comes from a single source "
                               "and could not be cross-checked just now.)"),
        "degraded_reply": ("I'm having a small technical problem right now and I "
                           "don't want to improvise. Please try again a little later."),
        "not_medical": "I am not a doctor and give no medical advice",
        "voice_privacy_notice": ("Browser voice may send what you say to "
                                 "Google/Apple services. For full privacy, use "
                                 "local voice (your own server)."),
        "ask_directive": (
            " ACTIVE RULE (conversation coherence dropped): do not introduce "
            "new information. Briefly restate what the person said and ask one "
            "single, warm clarifying question."),
    },
}

DEFAULT = "ro"


def t(locale: str, key: str, **kw) -> str:
    """Textul pentru (locale, key), cu fallback la DEFAULT, apoi format(**kw)."""
    loc = locale if locale in CATALOG else DEFAULT
    s = CATALOG[loc].get(key) or CATALOG[DEFAULT][key]
    return s.format(**kw) if kw else s


def bundle(locale: str) -> dict[str, str]:
    """Toate textele motorului pentru o limba (pt DualEngine)."""
    loc = locale if locale in CATALOG else DEFAULT
    return dict(CATALOG[loc])


def available() -> list[dict]:
    return [{"code": c, "name": CATALOG[c]["lang_name"], "speech": CATALOG[c]["speech"]}
            for c in CATALOG]

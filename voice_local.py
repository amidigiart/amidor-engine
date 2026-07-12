# -*- coding: utf-8 -*-
"""
Voce LOCALA (optionala) — calea GDPR-curata pentru instante pe server:
TTS prin piper (https://github.com/rhasspy/piper), rulat ca binar local.
Nicio silaba nu paraseste masina.

Configurare (env):
  PIPER_BIN        = calea catre executabilul piper
  PIPER_VOICE_RO   = calea catre modelul de voce .onnx pentru romana
  PIPER_VOICE_EN   = idem pentru engleza

Daca nu e configurat: /api/tts intoarce 501, iar interfata foloseste
speechSynthesis din browser — cu nota de confidentialitate afisata
(browserul poate trimite audio la Google/Apple; utilizatorul stie).
STT local (whisper) vine la deploy-ul pe server (Sprint 5) — are nevoie
de ffmpeg si modele; browserul acopera dezvoltarea si pilotul.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


def _voice_for(lang: str) -> str | None:
    return os.getenv(f"PIPER_VOICE_{lang.upper().split('-')[0]}")


def tts_available() -> dict:
    binp = os.getenv("PIPER_BIN")
    ok = bool(binp and Path(binp).exists())
    return {"piper": ok,
            "voices": {l: bool(_voice_for(l)) for l in ("ro", "en")}}


def synthesize(text: str, lang: str = "ro") -> bytes | None:
    """WAV din text, prin piper local. None daca neconfigurat/esec —
    apelantul decide fallback-ul (browser TTS cu nota de confidentialitate)."""
    binp = os.getenv("PIPER_BIN")
    voice = _voice_for(lang)
    if not (binp and voice and Path(binp).exists() and Path(voice).exists()):
        return None
    try:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.wav"
            subprocess.run([binp, "--model", voice, "--output_file", str(out)],
                           input=text.encode("utf-8"), timeout=60,
                           capture_output=True, check=True)
            return out.read_bytes()
    except Exception:
        return None

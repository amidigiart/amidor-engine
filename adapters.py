# -*- coding: utf-8 -*-
"""
Adapter universal pentru modele de limbaj — orice endpoint OpenAI-compatible:
Ollama local (/v1), Mistral, DeepSeek (open-weights self-hosted SAU API),
Grok, vLLM, LM Studio etc. Zero dependinte externe (doar stdlib).

Nota GDPR (din BLUEPRINT): pentru date personale UE, folositi endpointuri
UE sau self-hosted. API-urile non-UE (ex. DeepSeek China, Grok SUA) doar cu
temei legal si consimtamant explicit — decizia apartine operatorului.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass


class AdapterError(Exception):
    pass


@dataclass
class OpenAICompatAdapter:
    """Client minimal pentru /chat/completions."""
    base_url: str                  # ex. http://localhost:11434/v1
    model: str                     # ex. gemma3:4b, mistral-small-latest
    api_key: str | None = None
    temperature: float = 0.3
    max_tokens: int = 400
    timeout: int = 120
    name: str = ""                 # eticheta pentru loguri ("A", "mistral-eu"...)

    def complete(self, system: str, user: str) -> str:
        body = json.dumps({
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=body, headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read())
        except Exception as e:
            raise AdapterError(f"{self.name or self.model}: {e}") from e
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            raise AdapterError(f"{self.name or self.model}: raspuns invalid") from e


@dataclass
class CallableAdapter:
    """Adapter din orice functie (system, user) -> str. Pentru teste
    deterministe si pentru integrari custom."""
    fn: object
    name: str = "callable"

    def complete(self, system: str, user: str) -> str:
        return self.fn(system, user)

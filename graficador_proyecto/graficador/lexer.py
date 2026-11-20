"""Análisis léxico: convierte el texto en una lista de tokens."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import SintaxisError
from .funciones import FUNCIONES


@dataclass(frozen=True)
class Token:
    tipo: str      # NUM | ID | OP | LP | RP
    valor: str
    pos: int       # posición (base 0) en el texto original


_TOKEN = re.compile(
    r"""
      (?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)
    | (?P<id>(?![²³])[^\W\d](?:(?![²³])\w)*)
    | (?P<pot>\*\*)
    | (?P<op>[+\-*/^,])
    | (?P<lp>\()
    | (?P<rp>\))
    | (?P<esp>\s+)
    | (?P<otro>.)
    """,
    re.VERBOSE | re.DOTALL,
)

# Símbolos tipográficos que se aceptan como equivalentes
_EQUIVALENTES = {"×": "*", "·": "*", "÷": "/", "−": "-", "–": "-"}
_SUPERINDICES = {"²": "2", "³": "3"}


def tokenizar(texto: str) -> list[Token]:
    tokens: list[Token] = []
    for m in _TOKEN.finditer(texto):
        clase, valor, pos = m.lastgroup, m.group(), m.start()
        if clase == "esp":
            continue
        if clase == "num":
            tokens.append(Token("NUM", valor, pos))
        elif clase == "id":
            tokens.append(Token("ID", valor, pos))
        elif clase == "pot":
            tokens.append(Token("OP", "^", pos))
        elif clase == "op":
            tokens.append(Token("OP", valor, pos))
        elif clase == "lp":
            tokens.append(Token("LP", valor, pos))
        elif clase == "rp":
            tokens.append(Token("RP", valor, pos))
        elif valor in _EQUIVALENTES:
            tokens.append(Token("OP", _EQUIVALENTES[valor], pos))
        elif valor in _SUPERINDICES:
            tokens.append(Token("OP", "^", pos))
            tokens.append(Token("NUM", _SUPERINDICES[valor], pos))
        else:
            raise SintaxisError(f"Carácter no válido {valor!r}", pos)
    return _multiplicacion_implicita(tokens)


def _multiplicacion_implicita(tokens: list[Token]) -> list[Token]:
    """Inserta '*' en casos como 2x, 3(x+1), (x+1)(x-1) o 2sin(x)."""
    salida: list[Token] = []
    for t in tokens:
        if salida:
            prev = salida[-1]
            prev_es_valor = (
                prev.tipo in ("NUM", "RP")
                or (prev.tipo == "ID" and prev.valor not in FUNCIONES)
            )
            if prev_es_valor and t.tipo in ("NUM", "ID", "LP"):
                salida.append(Token("OP", "*", t.pos))
        salida.append(t)
    return salida

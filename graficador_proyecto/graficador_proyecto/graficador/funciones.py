"""Funciones y constantes disponibles en las expresiones.

Cada función valida su dominio y lanza DominioError con un mensaje claro en lugar
de devolver NaN o un número complejo. Para agregar una función nueva basta con
definirla aquí y registrarla en FUNCIONES; el lexer, el parser y el evaluador la
reconocen automáticamente.
"""

from __future__ import annotations

import math

from .errors import DominioError


def _fmt(x: float) -> str:
    return f"argumento = {x:.6g}"


def _sqrt(x: float) -> float:
    if x < 0:
        raise DominioError("raíz cuadrada de un número negativo", _fmt(x))
    return math.sqrt(x)


def _cbrt(x: float) -> float:
    # La raíz cúbica sí existe para negativos: cbrt(-8) = -2
    if hasattr(math, "cbrt"):
        return math.cbrt(x)
    return math.copysign(abs(x) ** (1.0 / 3.0), x)


def _ln(x: float) -> float:
    if x <= 0:
        raise DominioError("logaritmo de un número menor o igual a 0", _fmt(x))
    return math.log(x)


def _log10(x: float) -> float:
    if x <= 0:
        raise DominioError("logaritmo de un número menor o igual a 0", _fmt(x))
    return math.log10(x)


def _log2(x: float) -> float:
    if x <= 0:
        raise DominioError("logaritmo de un número menor o igual a 0", _fmt(x))
    return math.log2(x)


def _asin(x: float) -> float:
    if abs(x) > 1:
        raise DominioError("arcoseno de un valor fuera de [-1, 1]", _fmt(x))
    return math.asin(x)


def _acos(x: float) -> float:
    if abs(x) > 1:
        raise DominioError("arcocoseno de un valor fuera de [-1, 1]", _fmt(x))
    return math.acos(x)


FUNCIONES = {
    "sqrt": _sqrt,
    "cbrt": _cbrt,
    "abs": abs,
    "exp": math.exp,
    "ln": _ln,
    "log": _log10,
    "log2": _log2,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": _asin,
    "acos": _acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
}

CONSTANTES = {
    "pi": math.pi,
    "e": math.e,
}

"""Evaluación de un árbol de expresión en números reales (un punto a la vez).

Casos que se controlan explícitamente (nunca se devuelve NaN ni un complejo):

* raíz cuadrada de negativo, ln/log de x <= 0, asin/acos fuera de [-1, 1]
  -> DominioError
* división entre cero y 0 elevado a exponente negativo -> DivisionCeroError
* base negativa con exponente fraccionario:
    - si el exponente es racional con denominador impar, se usa la raíz real
      ((-8)^(1/3) = -2, (-8)^(2/3) = 4), igual que hacen las calculadoras gráficas;
    - en cualquier otro caso ((-4)^0.5, (-2)^pi) -> DominioError
* resultados infinitos o desbordamientos (exp(1000), 10^400) -> DominioError
"""

from __future__ import annotations

import math
from fractions import Fraction

from .errors import DivisionCeroError, DominioError, EvaluacionError, VariableError
from .funciones import CONSTANTES, FUNCIONES
from .nodes import Nodo


def evaluar(nodo: Nodo, valor: float | None = None, variable: str = "x") -> float:
    """Evalúa `nodo` con `variable = valor`. Devuelve un float real y finito."""
    x = None if valor is None else float(valor)
    try:
        return _ev(nodo, x, variable)
    except RecursionError:
        raise EvaluacionError("expresión demasiado anidada") from None


def _finito(v: float) -> float:
    if math.isnan(v) or math.isinf(v):
        raise DominioError("resultado no finito (desbordamiento numérico)")
    return v


def _raiz_real(base: float, exponente: float) -> float | None:
    """Potencia real de una base negativa si el exponente es p/q con q impar."""
    fr = Fraction(exponente).limit_denominator(1000)
    if abs(float(fr) - exponente) > 1e-12 * max(1.0, abs(exponente)):
        return None
    if fr.denominator % 2 == 0:
        return None
    magnitud = math.pow(abs(base), exponente)
    return -magnitud if fr.numerator % 2 != 0 else magnitud


def potencia(a: float, b: float) -> float:
    if a == 0:
        if b < 0:
            raise DivisionCeroError(
                "0 elevado a un exponente negativo (división entre cero)",
                f"0^{b:.6g}",
            )
        return 1.0 if b == 0 else 0.0
    try:
        if a < 0 and not float(b).is_integer():
            r = _raiz_real(a, b)
            if r is None:
                raise DominioError(
                    "potencia de base negativa con exponente no entero (no es real)",
                    f"({a:.6g})^({b:.6g})",
                )
            return r
        return math.pow(a, b)
    except OverflowError:
        raise DominioError("desbordamiento numérico en la potencia") from None


def _ev(n: Nodo, x: float | None, var: str) -> float:
    t = n.tipo
    if t == "num":
        return n.valor
    if t == "const":
        return CONSTANTES[n.valor]
    if t == "var":
        if n.valor != var:
            raise VariableError(f"Variable desconocida: {n.valor!r}")
        if x is None:
            raise VariableError(f"Falta el valor de la variable {var!r}")
        return x
    if t == "neg":
        return -_ev(n.hijos[0], x, var)
    if t == "func":
        arg = _ev(n.hijos[0], x, var)
        try:
            return _finito(FUNCIONES[n.valor](arg))
        except (ValueError, OverflowError):
            raise DominioError(
                f"{n.valor}() no está definida o se desborda", f"argumento = {arg:.6g}"
            ) from None
    if t == "func2":
        a2 = _ev(n.hijos[0], x, var)
        b2 = _ev(n.hijos[1], x, var)
        nombre = n.valor
        if nombre == "mod":
            if b2 == 0:
                raise DivisionCeroError("módulo entre cero", f"{a2:.6g} mod 0")
            return _finito(math.fmod(a2, b2))
        raise DominioError(f"Función binaria desconocida: {nombre}")

    a = _ev(n.hijos[0], x, var)
    b = _ev(n.hijos[1], x, var)
    op = n.valor
    try:
        if op == "+":
            r = a + b
        elif op == "-":
            r = a - b
        elif op == "*":
            r = a * b
        elif op == "/":
            if b == 0:
                raise DivisionCeroError("división entre cero", f"{a:.6g} / 0")
            r = a / b
        elif op == "^":
            r = potencia(a, b)
        else:  # pragma: no cover - el parser no genera otros operadores
            raise VariableError(f"Operador desconocido: {op}")
    except OverflowError:
        raise DominioError("desbordamiento numérico") from None
    return _finito(r)

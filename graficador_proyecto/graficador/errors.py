"""Excepciones del intérprete.

Jerarquía:

    ExpresionError
    ├── SintaxisError        la cadena está mal escrita
    ├── VariableError        variable desconocida, demasiadas variables o sin valor
    └── EvaluacionError      la expresión es válida pero no se puede calcular en ese punto
        ├── DominioError         p. ej. sqrt(-1), ln(0), asin(2), desbordamiento
        └── DivisionCeroError    p. ej. 1/0, 0^(-1)
"""

from __future__ import annotations


class ExpresionError(Exception):
    """Clase base de todos los errores del intérprete."""


class SintaxisError(ExpresionError):
    def __init__(self, mensaje: str, posicion: int | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.posicion = posicion          # índice base 0 dentro del texto

    def __str__(self) -> str:
        if self.posicion is None:
            return self.mensaje
        return f"{self.mensaje} (posición {self.posicion + 1})"


class VariableError(ExpresionError):
    """Variable desconocida, más de una variable, o falta su valor."""


class EvaluacionError(ExpresionError):
    """La expresión es correcta, pero no tiene valor real en ese punto."""

    def __init__(self, motivo: str, detalle: str | None = None):
        super().__init__(motivo if detalle is None else f"{motivo}: {detalle}")
        self.motivo = motivo              # texto corto, sin valores (sirve para agrupar)
        self.detalle = detalle


class DominioError(EvaluacionError):
    """Fuera del dominio real: raíz de negativo, log(0), asin(2), desbordamiento..."""


class DivisionCeroError(EvaluacionError):
    """División entre cero (incluye 0 elevado a un exponente negativo)."""

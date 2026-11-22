"""Análisis sintáctico: construye el árbol de expresión.

Gramática (de menor a mayor precedencia):

    expr   := term (('+' | '-') term)*
    term   := unary (('*' | '/') unary)*
    unary  := ('-' | '+') unary | power
    power  := atom ('^' unary)?            asociativa a la derecha: 2^3^2 = 2^(3^2)
    atom   := NUM | ID | ID '(' expr ')' | '(' expr ')'

Como `power` está por debajo de `unary`, -x^2 se lee como -(x^2), y el exponente
puede llevar signo: 2^-x.
"""

from __future__ import annotations

import math

from .errors import SintaxisError
from .funciones import CONSTANTES, FUNCIONES
from .lexer import Token, tokenizar
from .nodes import Nodo


class _Parser:
    def __init__(self, tokens: list[Token], texto: str):
        self.tokens = tokens
        self.i = 0
        self.fin = len(texto)

    # --- utilidades -------------------------------------------------------
    def _ver(self) -> Token | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def _tomar(self) -> Token:
        t = self._ver()
        if t is None:
            raise SintaxisError(
                "La expresión termina de forma inesperada: falta un operando", self.fin
            )
        self.i += 1
        return t

    def _es_op(self, *ops: str) -> bool:
        t = self._ver()
        return t is not None and t.tipo == "OP" and t.valor in ops

    def _cerrar(self, apertura: Token) -> None:
        t = self._ver()
        if t is None or t.tipo != "RP":
            raise SintaxisError("Falta cerrar el paréntesis '('", apertura.pos)
        self.i += 1

    # --- gramática ---------------------------------------------------------
    def parsear(self) -> Nodo:
        if not self.tokens:
            raise SintaxisError("La expresión está vacía")
        nodo = self._expr()
        t = self._ver()
        if t is not None:
            if t.tipo == "RP":
                raise SintaxisError("Paréntesis ')' sin abrir", t.pos)
            raise SintaxisError(f"Símbolo inesperado {t.valor!r}", t.pos)
        return nodo

    def _expr(self) -> Nodo:
        nodo = self._term()
        while self._es_op("+", "-"):
            op = self._tomar().valor
            nodo = Nodo("bin", op, [nodo, self._term()])
        return nodo

    def _term(self) -> Nodo:
        nodo = self._unary()
        while self._es_op("*", "/"):
            op = self._tomar().valor
            nodo = Nodo("bin", op, [nodo, self._unary()])
        return nodo

    def _unary(self) -> Nodo:
        if self._es_op("-"):
            self._tomar()
            return Nodo("neg", "-", [self._unary()])
        if self._es_op("+"):
            self._tomar()
            return self._unary()
        return self._power()

    def _power(self) -> Nodo:
        base = self._atom()
        if self._es_op("^"):
            self._tomar()
            return Nodo("bin", "^", [base, self._unary()])
        return base

    def _atom(self) -> Nodo:
        t = self._tomar()
        if t.tipo == "NUM":
            valor = float(t.valor)
            if not math.isfinite(valor):
                raise SintaxisError(f"Número fuera de rango: {t.valor}", t.pos)
            return Nodo("num", valor)
        if t.tipo == "ID":
            nombre = t.valor
            if nombre in FUNCIONES:
                apertura = self._ver()
                if apertura is None or apertura.tipo != "LP":
                    raise SintaxisError(
                        f"La función {nombre} necesita paréntesis: {nombre}(...)", t.pos
                    )
                self.i += 1
                argumento = self._expr()
                self._cerrar(apertura)
                return Nodo("func", nombre, [argumento])
            if nombre in CONSTANTES:
                return Nodo("const", nombre)
            return Nodo("var", nombre)
        if t.tipo == "LP":
            nodo = self._expr()
            self._cerrar(t)
            return nodo
        if t.tipo == "RP":
            raise SintaxisError("Se esperaba un valor antes de ')'", t.pos)
        raise SintaxisError(
            f"Se esperaba un número, una variable o '(' pero se encontró {t.valor!r}",
            t.pos,
        )


def construir_arbol(texto: str) -> Nodo:
    """Convierte una expresión en su árbol de expresión."""
    try:
        return _Parser(tokenizar(texto), texto).parsear()
    except RecursionError:
        raise SintaxisError("La expresión está demasiado anidada") from None

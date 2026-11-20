"""Generador de ecuaciones aleatorias a partir de una biblioteca de operadores.

La biblioteca define qué operadores y funciones están disponibles.
El generador construye un árbol de expresión aleatorio respetando la
altura máxima configurada, y lo serializa a texto para que el parser
existente lo procese sin cambios.

Operadores soportados
---------------------
Binarios : +  -  *  /  ^  %   (módulo: a % b implementado como mod())
Unarios  : sqrt  log  sin  cos  tan
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable


# ---------------------------------------------------------------------------
# Definición de la biblioteca
# ---------------------------------------------------------------------------

@dataclass
class EntradaOperador:
    """Descripción de un operador/función dentro de la biblioteca."""
    clave: str          # identificador interno único
    etiqueta: str       # texto que se muestra en la interfaz
    aridad: int         # 1 = unario, 2 = binario
    simbolo: str        # símbolo para serializar a texto: "+" / "sin" / "mod" …
    peso: float = 1.0   # probabilidad relativa de ser escogido (mayor = más probable)
    descripcion: str = ""

    def __hash__(self):
        return hash(self.clave)


# Catálogo completo de operadores disponibles
CATALOGO: dict[str, EntradaOperador] = {
    "suma":   EntradaOperador("suma",   "Suma ( + )",            2, "+",    peso=2.0, descripcion="a + b"),
    "resta":  EntradaOperador("resta",  "Resta ( − )",           2, "-",    peso=2.0, descripcion="a − b"),
    "mult":   EntradaOperador("mult",   "Multiplicación ( × )",  2, "*",    peso=2.0, descripcion="a × b"),
    "div":    EntradaOperador("div",    "División ( / )",         2, "/",    peso=1.0, descripcion="a / b"),
    "pot":    EntradaOperador("pot",    "Potencia ( ^ )",         2, "^",    peso=1.0, descripcion="a ^ b"),
    "mod":    EntradaOperador("mod",    "Módulo ( % )",           2, "mod",  peso=0.8, descripcion="mod(a,b)"),
    "sqrt":   EntradaOperador("sqrt",   "Raíz cuadrada √",       1, "sqrt", peso=1.0, descripcion="sqrt(x)"),
    "log":    EntradaOperador("log",    "Logaritmo base 10",      1, "log",  peso=0.8, descripcion="log(x)"),
    "sin":    EntradaOperador("sin",    "Seno",                   1, "sin",  peso=1.0, descripcion="sin(x)"),
    "cos":    EntradaOperador("cos",    "Coseno",                 1, "cos",  peso=1.0, descripcion="cos(x)"),
    "tan":    EntradaOperador("tan",    "Tangente",               1, "tan",  peso=0.6, descripcion="tan(x)"),
}

# Subconjunto activo por defecto
CLAVES_DEFECTO = {"suma", "resta", "mult", "pot", "sin", "cos"}


# ---------------------------------------------------------------------------
# Generador de ecuaciones
# ---------------------------------------------------------------------------

class GeneradorEcuaciones:
    """Genera expresiones matemáticas aleatorias como cadenas de texto.

    Parameters
    ----------
    operadores:
        Conjunto de claves del CATALOGO habilitadas.
    max_altura:
        Altura máxima del árbol (1 = solo hoja, 2 = un nivel de operación, …).
    prob_variable:
        Probabilidad de que una hoja sea ``x`` en lugar de una constante.
    rango_constante:
        Rango (a, b) del que se toman constantes reales aleatorias.
    semilla:
        Si no es None, fija la semilla del generador aleatorio.
    """

    def __init__(
        self,
        operadores: set[str] | None = None,
        max_altura: int = 4,
        prob_variable: float = 0.6,
        rango_constante: tuple[float, float] = (1.0, 10.0),
        semilla: int | None = None,
    ):
        self.operadores: set[str] = operadores if operadores is not None else set(CLAVES_DEFECTO)
        self.max_altura = max(1, max_altura)
        self.prob_variable = prob_variable
        self.rango_constante = rango_constante
        self._rng = random.Random(semilla)

    # ------------------------------------------------------------------ API
    def generar(self) -> str:
        """Devuelve una expresión aleatoria como cadena de texto parseable."""
        arbol = self._nodo(self.max_altura)
        expr = self._serializar(arbol)
        # Garantizar que x aparece al menos una vez (si hay operadores disponibles)
        if "x" not in expr and self.operadores:
            expr = f"({expr}) + 0*x"
        return expr

    # ---------------------------------------------------------------- interno
    def _ops_binarios(self) -> list[EntradaOperador]:
        return [CATALOGO[k] for k in self.operadores if CATALOGO[k].aridad == 2]

    def _ops_unarios(self) -> list[EntradaOperador]:
        return [CATALOGO[k] for k in self.operadores if CATALOGO[k].aridad == 1]

    def _elegir(self, lista: list[EntradaOperador]) -> EntradaOperador:
        pesos = [e.peso for e in lista]
        return self._rng.choices(lista, weights=pesos, k=1)[0]

    def _constante(self) -> float:
        a, b = self.rango_constante
        # 50% entero pequeño, 50% decimal con 2 decimales
        if self._rng.random() < 0.5:
            return float(self._rng.randint(1, max(1, int(b))))
        return round(self._rng.uniform(a, b), 2)

    def _nodo(self, altura: int) -> dict:
        """Genera un nodo del árbol (como dict) con la altura dada."""
        bins = self._ops_binarios()
        unis = self._ops_unarios()

        # En hojas (altura ≤ 1) o si no hay operadores: leaf
        if altura <= 1 or (not bins and not unis):
            return self._hoja()

        # Decidir si poner un operador o una hoja (más probable operador cuanto mayor la altura)
        prob_hoja = 0.15 if altura >= self.max_altura else 0.25
        if self._rng.random() < prob_hoja:
            return self._hoja()

        # Elegir tipo de operador
        tiene_bin = bool(bins)
        tiene_uni = bool(unis)
        if tiene_bin and tiene_uni:
            es_bin = self._rng.random() < 0.65
        else:
            es_bin = tiene_bin

        if es_bin:
            op = self._elegir(bins)
            return {"tipo": "bin", "op": op,
                    "izq": self._nodo(altura - 1),
                    "der": self._nodo(altura - 1)}
        else:
            op = self._elegir(unis)
            return {"tipo": "uni", "op": op,
                    "hijo": self._nodo(altura - 1)}

    def _hoja(self) -> dict:
        if self._rng.random() < self.prob_variable:
            return {"tipo": "var"}
        c = self._constante()
        return {"tipo": "num", "val": c}

    # ---------------------------------------------------------------- serial
    def _serializar(self, nodo: dict) -> str:
        t = nodo["tipo"]
        if t == "var":
            return "x"
        if t == "num":
            v = nodo["val"]
            return str(int(v)) if float(v).is_integer() else str(v)
        if t == "uni":
            op: EntradaOperador = nodo["op"]
            hijo = self._serializar(nodo["hijo"])
            return f"{op.simbolo}({hijo})"
        # binario
        op = nodo["op"]
        izq = self._serializar(nodo["izq"])
        der = self._serializar(nodo["der"])

        if op.simbolo == "mod":
            # El parser no tiene %, se implementa como mod(a,b) via función registrada
            return f"mod({izq},{der})"
        if op.simbolo == "^":
            # Exponent: siempre poner paréntesis alrededor de la base si es compuesta
            base = f"({izq})" if _es_compuesto(nodo["izq"]) else izq
            exp  = f"({der})" if _es_compuesto(nodo["der"])  else der
            return f"{base}^{exp}"
        # + - *  /
        izq_p = f"({izq})" if _necesita_paren_izq(nodo["izq"], op.simbolo) else izq
        der_p = f"({der})" if _necesita_paren_der(nodo["der"], op.simbolo) else der
        return f"{izq_p}{op.simbolo}{der_p}"


# ---------------------------------------------------------------------------
# Helpers de serialización (mínimos paréntesis necesarios)
# ---------------------------------------------------------------------------

_PREC = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}


def _prec(simbolo: str) -> int:
    return _PREC.get(simbolo, 4)


def _es_compuesto(nodo: dict) -> bool:
    return nodo["tipo"] in ("bin", "uni")


def _necesita_paren_izq(nodo: dict, op_padre: str) -> bool:
    if nodo["tipo"] != "bin":
        return False
    return _prec(nodo["op"].simbolo) < _prec(op_padre)


def _necesita_paren_der(nodo: dict, op_padre: str) -> bool:
    if nodo["tipo"] != "bin":
        return False
    p_hijo = _prec(nodo["op"].simbolo)
    p_padre = _prec(op_padre)
    if p_hijo < p_padre:
        return True
    # Misma precedencia: - y / NO son conmutativos → paréntesis
    if p_hijo == p_padre and op_padre in ("-", "/"):
        return True
    return False

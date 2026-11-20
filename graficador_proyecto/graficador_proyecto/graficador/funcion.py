"""Interfaz de alto nivel: una expresión como objeto reutilizable."""

from __future__ import annotations

from .errors import VariableError
from .evaluador import evaluar
from .nodes import Nodo, variables
from .parser import construir_arbol
from .sampling import Muestra, muestrear
from .tree_text import a_texto, arbol_ascii


class Funcion:
    """Función de una variable definida por una expresión de texto.

    >>> f = Funcion("sqrt(2*(x^2)+5*x-3)")
    >>> f(1)
    2.0
    >>> print(f.arbol_ascii())      # árbol de expresión
    >>> m = f.muestrear(-10, 10)    # puntos listos para graficar
    """

    def __init__(self, texto: str):
        self.texto = texto
        self.arbol: Nodo = construir_arbol(texto)
        nombres = sorted(variables(self.arbol))
        if len(nombres) > 1:
            raise VariableError(
                "Solo se puede graficar con una variable; se encontraron: "
                + ", ".join(nombres)
            )
        self.variable = nombres[0] if nombres else "x"

    def __call__(self, valor: float) -> float:
        """Evalúa f(valor). Lanza DominioError / DivisionCeroError si no es real."""
        return evaluar(self.arbol, valor, self.variable)

    def muestrear(self, xmin: float, xmax: float, n: int = 800) -> Muestra:
        return muestrear(self, xmin, xmax, n)

    def arbol_ascii(self) -> str:
        return arbol_ascii(self.arbol)

    def forma_parentizada(self) -> str:
        return a_texto(self.arbol)

    def __repr__(self) -> str:
        return f"Funcion({self.texto!r})"


def evaluar_constante(texto: str) -> float:
    """Evalúa una expresión sin variables (para los límites del intervalo).

    Acepta operaciones, funciones y constantes: "-2*pi", "sqrt(2)", "1/3".
    """
    arbol = construir_arbol(texto)
    if variables(arbol):
        raise VariableError("Debe ser un número o una expresión sin variables (ej. -2*pi)")
    return evaluar(arbol)

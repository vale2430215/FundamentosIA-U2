"""Intérprete de expresiones matemáticas con árbol de expresión y graficación.

Núcleo (Python puro, sin dependencias):

    from graficador import Funcion
    f = Funcion("sqrt(2*(x^2)+5*x-3)")
    f(1)                      # 2.0
    print(f.arbol_ascii())    # árbol de expresión
    m = f.muestrear(-10, 10)  # puntos, dominio y asíntotas

Las partes que usan matplotlib / tkinter (tree_draw, plotting, sesion, gui, cli)
se importan solo cuando hacen falta.
"""

from .errors import (DivisionCeroError, DominioError, EvaluacionError,
                     ExpresionError, SintaxisError, VariableError)
from .evaluador import evaluar
from .funcion import Funcion, evaluar_constante
from .nodes import Nodo, variables
from .parser import construir_arbol
from .sampling import IntervaloIndefinido, Muestra, muestrear
from .tree_text import a_texto, arbol_ascii

__all__ = [
    "Funcion", "evaluar_constante", "construir_arbol", "evaluar",
    "muestrear", "Muestra", "IntervaloIndefinido",
    "arbol_ascii", "a_texto", "Nodo", "variables",
    "ExpresionError", "SintaxisError", "VariableError", "EvaluacionError",
    "DominioError", "DivisionCeroError",
]

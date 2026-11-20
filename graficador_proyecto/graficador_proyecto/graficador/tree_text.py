"""Representaciones en texto del árbol de expresión."""

from __future__ import annotations

from .nodes import Nodo


def a_texto(nodo: Nodo) -> str:
    """Reconstruye la expresión con todos los paréntesis que impone el árbol."""
    if nodo.tipo in ("num", "var", "const"):
        return nodo.etiqueta
    if nodo.tipo == "neg":
        return f"(-{a_texto(nodo.hijos[0])})"
    if nodo.tipo == "func":
        return f"{nodo.valor}({a_texto(nodo.hijos[0])})"
    if nodo.tipo == "func2":
        return f"{nodo.valor}({a_texto(nodo.hijos[0])}, {a_texto(nodo.hijos[1])})"
    izq, der = nodo.hijos
    return f"({a_texto(izq)} {nodo.valor} {a_texto(der)})"


def arbol_ascii(nodo: Nodo, prefijo: str = "", es_ultimo: bool = True,
                es_raiz: bool = True) -> str:
    """Dibuja el árbol con caracteres de caja (estilo comando `tree`)."""
    if es_raiz:
        lineas = [nodo.etiqueta]
        nuevo = ""
    else:
        lineas = [prefijo + ("└── " if es_ultimo else "├── ") + nodo.etiqueta]
        nuevo = prefijo + ("    " if es_ultimo else "│   ")
    for k, h in enumerate(nodo.hijos):
        lineas.append(arbol_ascii(h, nuevo, k == len(nodo.hijos) - 1, False))
    return "\n".join(lineas)

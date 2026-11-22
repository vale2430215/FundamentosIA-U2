"""Dibujo del árbol de expresión sobre un eje de matplotlib.

Solo necesita un objeto `Axes`; no importa matplotlib por sí mismo, así que puede
usarse con pyplot, con `Figure` embebida en tkinter, con Agg, etc.
"""

from __future__ import annotations

from .nodes import Nodo, contar_hojas

_COLORES = {
    "num": "#cfe8ff",
    "var": "#d6f5d6",
    "const": "#e8d9ff",
    "bin": "#ffe3b3",
    "neg": "#ffe3b3",
    "func": "#ffd0d0",
}


def _posiciones(nodo: Nodo, profundidad: int, siguiente: list[float],
                pos: dict[int, tuple[float, int]]) -> float:
    if not nodo.hijos:
        x = siguiente[0]
        siguiente[0] += 1
    else:
        xs = [_posiciones(h, profundidad + 1, siguiente, pos) for h in nodo.hijos]
        x = sum(xs) / len(xs)
    pos[id(nodo)] = (x, profundidad)
    return x


def dibujar_arbol(nodo: Nodo, ax, titulo: str = "Árbol de expresión") -> None:
    pos: dict[int, tuple[float, int]] = {}
    _posiciones(nodo, 0, [0.0], pos)
    hojas = contar_hojas(nodo)
    tam = max(6.5, min(11.0, 120.0 / max(hojas, 1)))     # letra más chica en árboles grandes

    def aristas(n: Nodo) -> None:
        x0, y0 = pos[id(n)]
        for h in n.hijos:
            x1, y1 = pos[id(h)]
            ax.plot([x0, x1], [-y0, -y1], color="#666666", lw=1.2, zorder=1)
            aristas(h)

    def nodos(n: Nodo) -> None:
        x, y = pos[id(n)]
        ax.text(x, -y, n.etiqueta, ha="center", va="center", fontsize=tam, zorder=2,
                bbox=dict(boxstyle="round,pad=0.35", fc=_COLORES[n.tipo], ec="#444444"))
        for h in n.hijos:
            nodos(h)

    aristas(nodo)
    nodos(nodo)
    ax.set_title(titulo)
    ax.margins(0.12)
    ax.axis("off")

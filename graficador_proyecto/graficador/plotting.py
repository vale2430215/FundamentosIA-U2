"""Gráfica animada: la curva se va trazando punto por punto.

`GraficaPorPuntos` no depende de ninguna interfaz: solo recibe un `Axes` y una
`Muestra`. Quien la use (tkinter, un script, un notebook, un GIF) decide cuándo
llamar a `avanzar()`:

    anim = GraficaPorPuntos(ax, muestra, "y = sin(x)")
    while not anim.avanzar(5):       # dibuja 5 puntos más por llamada
        canvas.draw_idle()
"""

from __future__ import annotations

import math

from .sampling import Muestra


class GraficaPorPuntos:
    COLOR_CURVA = "#1f77b4"
    COLOR_CABEZA = "#d62728"
    COLOR_ASINTOTA = "#d62728"
    COLOR_ZONA = "#999999"

    def __init__(self, ax, muestra: Muestra, titulo: str = "", variable: str = "x"):
        self.ax = ax
        self.m = muestra
        self.titulo = titulo
        self.variable = variable
        self._k = 0
        self.preparar()

    # ------------------------------------------------------------------
    def preparar(self) -> None:
        """Deja el eje vacío (con ejes, rejilla y límites) listo para animar."""
        ax, m = self.ax, self.m
        ax.clear()
        ax.set_autoscale_on(False)
        margen = 0.02 * (m.xmax - m.xmin)
        ax.set_xlim(m.xmin - margen, m.xmax + margen)
        ax.set_ylim(m.ymin, m.ymax)
        ax.axhline(0, color="#888888", lw=0.8, zorder=1)
        ax.axvline(0, color="#888888", lw=0.8, zorder=1)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel(self.variable)
        ax.set_ylabel(f"f({self.variable})")
        ax.set_title(self.titulo)

        self._zonas = []
        for iv in m.indefinidos:
            if iv.fin > iv.inicio:
                art = ax.axvspan(iv.inicio, iv.fin, color=self.COLOR_ZONA, alpha=0.18,
                                 zorder=0, visible=False)
                self._zonas.append((iv.inicio, art))

        self._asintotas = []
        for x in m.asintotas:
            art = ax.axvline(x, color=self.COLOR_ASINTOTA, ls="--", lw=1, alpha=0.7,
                             zorder=2, visible=False)
            self._asintotas.append((x, art))

        (self._linea,) = ax.plot([], [], color=self.COLOR_CURVA, lw=2, zorder=3)
        (self._cabeza,) = ax.plot([], [], "o", color=self.COLOR_CABEZA, ms=6, zorder=4)

        if m.n_validos == 0:
            ax.text(0.5, 0.5, "La expresión no tiene valores reales\nen el intervalo indicado",
                    transform=ax.transAxes, ha="center", va="center", fontsize=12)
        self._k = 0

    # ------------------------------------------------------------------
    @property
    def total(self) -> int:
        return len(self.m.xs)

    @property
    def progreso(self) -> float:
        return 1.0 if self.total == 0 else self._k / self.total

    @property
    def terminada(self) -> bool:
        return self._k >= self.total

    def avanzar(self, n: int = 1) -> bool:
        """Revela `n` puntos más. Devuelve True cuando ya se dibujó todo."""
        total = self.total
        self._k = min(total, self._k + max(1, int(n)))
        k = self._k
        xs, ys = self.m.xs, self.m.ys

        self._linea.set_data(xs[:k], ys[:k])

        i = k - 1
        while i >= 0 and math.isnan(ys[i]):
            i -= 1
        if i >= 0 and k < total:
            self._cabeza.set_data([xs[i]], [ys[i]])
        else:
            self._cabeza.set_data([], [])

        x_actual = xs[k - 1] if k else self.m.xmin
        for x, art in self._asintotas:
            if x <= x_actual:
                art.set_visible(True)
        for inicio, art in self._zonas:
            if inicio <= x_actual:
                art.set_visible(True)
        return k >= total

    def terminar(self) -> None:
        """Salta al final de la animación."""
        self.avanzar(self.total)

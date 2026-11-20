"""Lógica de una sesión de graficación, independiente de la interfaz.

La ventana (gui.py) solo lee los campos de texto, llama a `Sesion.iniciar()` y
luego a `Sesion.avanzar()` en cada tic del temporizador. Así toda la validación
de entradas y el flujo de la animación se pueden probar sin abrir ninguna ventana.
"""

from __future__ import annotations

import csv
import math

from .errors import ExpresionError
from .funcion import Funcion, evaluar_constante
from .metrics import Metricas, calcular as calcular_metricas
from .plotting import GraficaPorPuntos
from .tree_draw import dibujar_arbol

MIN_PUNTOS = 2
MAX_PUNTOS = 25000          # aumentado para soportar 20 001 puntos (paso 0.001)


class ErrorEntrada(Exception):
    """Algún campo del formulario no es válido (el mensaje se muestra al usuario)."""


class Sesion:
    def __init__(self, ax_arbol, ax_grafica):
        self.ax_arbol = ax_arbol
        self.ax_grafica = ax_grafica
        self.funcion: Funcion | None = None
        self.animacion: GraficaPorPuntos | None = None
        # Datos guardados para exportar CSV y calcular métricas
        self._xs_validos: list[float] = []
        self._ys_exactos: list[float] = []
        self.metricas: Metricas | None = None

    # ------------------------------------------------------------------
    def iniciar(self, expresion: str, txt_xmin: str, txt_xmax: str,
                txt_puntos: str) -> list[str]:
        """Valida las entradas, dibuja el árbol y deja lista la animación.

        Devuelve las líneas de información para mostrar (expresión interpretada,
        dominio, asíntotas). Lanza ErrorEntrada si algo no es válido; en ese caso
        el estado anterior (árbol y gráfica) no se modifica.
        """
        try:
            f = Funcion(expresion.strip())
        except ExpresionError as e:
            raise ErrorEntrada(f"Error en la ecuación: {e}") from None

        try:
            xmin = evaluar_constante(txt_xmin)
        except ExpresionError as e:
            raise ErrorEntrada(f"Límite inferior no válido: {e}") from None
        try:
            xmax = evaluar_constante(txt_xmax)
        except ExpresionError as e:
            raise ErrorEntrada(f"Límite superior no válido: {e}") from None
        if not xmin < xmax:
            raise ErrorEntrada("El límite inferior debe ser menor que el superior.")

        try:
            n = int(str(txt_puntos).strip())
        except ValueError:
            raise ErrorEntrada("El número de puntos debe ser un entero.") from None
        if not MIN_PUNTOS <= n <= MAX_PUNTOS:
            raise ErrorEntrada(f"El número de puntos debe estar entre {MIN_PUNTOS} y {MAX_PUNTOS}.")

        muestra = f.muestrear(xmin, xmax, n)

        # Guardar pares (x, y) válidos para CSV y métricas
        xs_v = [x for x, y in zip(muestra.xs, muestra.ys) if not math.isnan(y)]
        ys_v = [y for y in muestra.ys if not math.isnan(y)]
        self._xs_validos = xs_v
        self._ys_exactos = ys_v
        self.metricas = None       # se calculará al exportar el CSV

        self.funcion = f
        self.ax_arbol.clear()
        dibujar_arbol(f.arbol, self.ax_arbol)
        self.animacion = GraficaPorPuntos(
            self.ax_grafica, muestra, f"y = {f.texto.strip()}", f.variable)

        return [f"Interpretada como: {f.forma_parentizada()}",
                f"Variable: {f.variable}   |   puntos: {n}   |   válidos: {len(xs_v)}"
                ] + muestra.resumen()

    # ------------------------------------------------------------------
    @property
    def activa(self) -> bool:
        return self.animacion is not None

    def avanzar(self, paso: int) -> bool:
        """Revela `paso` puntos más. True cuando la curva ya está completa."""
        if self.animacion is None:
            return True
        return self.animacion.avanzar(paso)

    def completar(self) -> None:
        if self.animacion is not None:
            self.animacion.terminar()

    def exportar_csv(self, ruta: str, decimales: int = 6) -> Metricas:
        """Escribe los puntos válidos en un CSV y devuelve las métricas de error.

        El CSV tiene encabezado ``x,y`` y los valores se redondean a `decimales`
        cifras decimales (por defecto 6). Las métricas comparan los valores
        exactos (guardados en `_ys_exactos`) con los leídos de vuelta desde el
        CSV (Opción A: error de representación numérica).
        """
        if not self._xs_validos:
            raise ValueError("No hay datos que exportar. Grafica primero una expresión.")

        fmt = f"{{:.{decimales}f}}"

        # Escribir CSV
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y"])
            for x, y in zip(self._xs_validos, self._ys_exactos):
                writer.writerow([fmt.format(x), fmt.format(y)])

        # Leer de vuelta los valores de y del CSV (simulando la pérdida de precisión)
        ys_csv: list[float] = []
        with open(ruta, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ys_csv.append(float(row["y"]))

        self.metricas = calcular_metricas(self._ys_exactos, ys_csv)
        return self.metricas

    def limpiar(self) -> None:
        self.animacion = None
        self.funcion = None
        self._xs_validos = []
        self._ys_exactos = []
        self.metricas = None
        self.ax_arbol.clear()
        self.ax_grafica.clear()

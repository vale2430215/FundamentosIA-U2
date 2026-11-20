"""
PROYECTO 2 - VISUALIZADOR INTERACTIVO
=====================================
AG con codificacion REAL (ag_real.py) sobre las funciones de prueba del libro
(funciones.py), en una ventana:

  - Pestaña "Visualizador": recorre la ejecucion generacion por generacion.
  - Pestaña "Individuos":   tabla de la generacion actual.
  - Pestaña "Comparar cruces": corre los 4 cruces (un punto, discreto uniforme,
    aritmetico y SBX) varias veces con las mismas semillas y compara su convergencia.

Ejecutar:
    python app_proyecto2.py
"""

import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.dirname(AQUI))  # para importar visor_ag.py

import numpy as np  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ag_real import TIPOS_CRUCE, algoritmo_genetico  # noqa: E402
from funciones import FUNCIONES_MAX, FUNCIONES_MIN, FUNCIONES_VARIAS, obtener_funcion  # noqa: E402
from visor_ag import (C_ABS, C_FUNCION, C_INDIV, C_MEJOR, INK, Resultado, VentanaAG,  # noqa: E402
                      iniciar, lienzo)

NOMBRE_CRUCE = {"un_punto": "Un punto", "uniforme": "Discreto uniforme",
                "aritmetico": "Aritmético", "sbx": "SBX"}
COLOR_CRUCE = {"un_punto": C_FUNCION, "uniforme": C_INDIV, "aritmetico": C_ABS, "sbx": C_MEJOR}
CON_N = {"rastrigin", "michalewicz", "schwefel"}  # funciones con numero de variables libre


def spin(minimo, maximo, valor, paso=1.0, decimales=None):
    if decimales is None:
        w = QSpinBox()
    else:
        w = QDoubleSpinBox()
        w.setDecimals(decimales)
    w.setRange(minimo, maximo)
    w.setSingleStep(paso)
    w.setValue(valor)
    return w


def correr(p, progreso):
    config = obtener_funcion(p["funcion"], p["n"])
    res = algoritmo_genetico(config, p["tam_pob"], p["num_gen"], p["prob_cruce"], p["prob_mut"],
                             p["cruce"], p["elitismo"], p["semilla"], progreso=progreso)
    f = config["f"]
    pobs = [res["poblaciones"][g] for g in range(p["num_gen"] + 1)]
    valores = [np.array([f(x) for x in pob]) for pob in pobs]
    titulo = (f"Proyecto 2 · {config['nombre']}  (AG real, cruce {NOMBRE_CRUCE[p['cruce']]})   "
              f"{config['texto']}")
    return Resultado(titulo=titulo, funcion=f, x_min=config["x_min"], x_max=config["x_max"],
                     maximizar=config["tipo"] == "max", poblaciones=pobs, valores=valores,
                     optimo=config["optimo"], x_opt=config["x_opt"])


def comparar(p, ejecuciones, progreso):
    """Corre los 4 cruces con las mismas semillas y devuelve sus historiales."""
    config = obtener_funcion(p["funcion"], p["n"])
    base = p["semilla"] if p["semilla"] is not None else int(time.time()) % 100000
    total, hechas = len(TIPOS_CRUCE) * ejecuciones, 0
    datos = {}
    for cruce in TIPOS_CRUCE:
        hist = []
        for s in range(ejecuciones):
            r = algoritmo_genetico(config, p["tam_pob"], p["num_gen"], p["prob_cruce"],
                                   p["prob_mut"], cruce, p["elitismo"], base + s)
            hist.append(r["hist_mejor_absoluto"])
            hechas += 1
            progreso(hechas / total)
        datos[cruce] = np.array(hist)
    return config, datos, ejecuciones


class PestanaComparar(QWidget):
    def __init__(self, ventana):
        super().__init__()
        self.ventana = ventana
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)

        fila = QHBoxLayout()
        fila.addWidget(QLabel("Ejecuciones por cruce"))
        self.ejecuciones = spin(1, 50, 5)
        fila.addWidget(self.ejecuciones)
        self.btn = QPushButton("Comparar los 4 cruces")
        self.btn.setObjectName("primary")
        self.btn.clicked.connect(self.correr)
        fila.addWidget(self.btn)
        nota = QLabel("Usa la función y los parámetros del panel izquierdo. Cada cruce se corre con "
                      "las mismas semillas para que la comparación sea justa.")
        nota.setObjectName("subtitulo")
        nota.setWordWrap(True)
        fila.addWidget(nota, 1)
        lay.addLayout(fila)

        self.fig, self.canvas = lienzo((10, 5))
        lay.addWidget(self.canvas, 3)

        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setMaximumHeight(170)
        lay.addWidget(self.tabla, 1)

    def correr(self):
        try:
            p = self.ventana.leer_parametros()
        except ValueError:
            return
        self.btn.setEnabled(False)
        self.ventana.lanzar(comparar, (p, self.ejecuciones.value()), self.mostrar)
        self.ventana.trabajador.finished.connect(lambda: self.btn.setEnabled(True))

    def mostrar(self, salida):
        config, datos, ejec = salida
        self.ventana.barra.setValue(100)
        fig = self.fig
        fig.clear()
        ax1, ax2 = fig.subplots(1, 2, width_ratios=[2, 1])
        for cruce in TIPOS_CRUCE:
            h = datos[cruce]
            gens = np.arange(h.shape[1])
            ax1.plot(gens, h.mean(axis=0), color=COLOR_CRUCE[cruce], lw=2, label=NOMBRE_CRUCE[cruce])
            if ejec > 1:
                ax1.fill_between(gens, np.percentile(h, 25, axis=0), np.percentile(h, 75, axis=0),
                                 color=COLOR_CRUCE[cruce], alpha=0.12)
        if config["optimo"] is not None:
            ax1.axhline(config["optimo"], color=INK, ls=":", lw=0.9, label="Óptimo (libro)")
        ax1.set_xlabel("Generación")
        ax1.set_ylabel("Mejor f(x) encontrado (media)")
        ax1.set_title("Convergencia" + (" (banda = cuartiles 25-75 %)" if ejec > 1 else ""), loc="left")
        ax1.legend(framealpha=0.9)

        finales = [datos[c][:, -1] for c in TIPOS_CRUCE]
        bp = ax2.boxplot(finales, patch_artist=True, widths=0.55,
                         medianprops=dict(color="black"), whiskerprops=dict(color=INK),
                         capprops=dict(color=INK), flierprops=dict(markeredgecolor=INK))
        for caja, c in zip(bp["boxes"], TIPOS_CRUCE):
            caja.set_facecolor(COLOR_CRUCE[c])
            caja.set_edgecolor(INK)
        ax2.set_xticks(range(1, 5))
        ax2.set_xticklabels([NOMBRE_CRUCE[c] for c in TIPOS_CRUCE], rotation=15)
        if config["optimo"] is not None:
            ax2.axhline(config["optimo"], color=INK, ls=":", lw=0.9)
        ax2.set_title("Resultado final", loc="left")
        fig.suptitle(f"{config['nombre']} (n = {config['n']}) · {ejec} ejecuciones por cruce   "
                     f"{config['texto']}", fontsize=11, fontweight="bold")
        self.canvas.draw_idle()

        columnas = ["Cruce", "Media final", "Mejor", "Peor", "Desv. est.", "Error medio vs. libro"]
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setRowCount(len(TIPOS_CRUCE))
        maxi = config["tipo"] == "max"
        for fila, c in enumerate(TIPOS_CRUCE):
            v = datos[c][:, -1]
            err = "—" if config["optimo"] is None else f"{np.mean(np.abs(v - config['optimo'])):.6g}"
            celdas = [NOMBRE_CRUCE[c], f"{v.mean():.6f}", f"{(v.max() if maxi else v.min()):.6f}",
                      f"{(v.min() if maxi else v.max()):.6f}", f"{v.std():.6f}", err]
            for col, d in enumerate(celdas):
                item = QTableWidgetItem(d)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(fila, col, item)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


class VentanaProyecto2(VentanaAG):
    def __init__(self):
        super().__init__("Proyecto 2 · AG real",
                         "Algoritmos Evolutivos (Araujo y Cervigon) · codificación real con "
                         "cruce de un punto, uniforme, aritmético y SBX")
        self.comparar = PestanaComparar(self)
        self.tabs.addTab(self.comparar, "Comparar cruces")

    def construir_parametros(self):
        self.funcion = QComboBox()
        for grupo, nombres in [("Máx.", FUNCIONES_MAX), ("Mín.", FUNCIONES_MIN),
                               ("Varias var.", FUNCIONES_VARIAS)]:
            for nombre in nombres:
                self.funcion.addItem(f"{nombre}   ({grupo})", nombre)
        self.funcion.setCurrentIndex(self.funcion.findData("rastrigin"))
        self.n = spin(1, 30, 2)
        self.n.setToolTip("Número de variables (solo rastrigin, michalewicz y schwefel)")
        self.cruce = QComboBox()
        for c in TIPOS_CRUCE:
            self.cruce.addItem(NOMBRE_CRUCE[c], c)
        self.cruce.setCurrentIndex(TIPOS_CRUCE.index("sbx"))
        self.tam_pob = spin(4, 5000, 100, 10)
        self.num_gen = spin(1, 5000, 100, 10)
        self.prob_cruce = spin(0.0, 1.0, 0.6, 0.05, 3)
        self.prob_mut = spin(0.0, 1.0, 0.05, 0.005, 3)
        self.elitismo = QCheckBox("Elitismo (2 %)")
        self.elitismo.setChecked(True)
        self.semilla = spin(-1, 999999, -1)
        self.semilla.setSpecialValueText("aleatoria")
        self.semilla.setToolTip("Fija una semilla para repetir exactamente la misma ejecución")

        for etiqueta, w in [("Función", self.funcion), ("Nº de variables", self.n),
                            ("Cruce", self.cruce), ("Tamaño población", self.tam_pob),
                            ("Generaciones", self.num_gen), ("Prob. de cruce", self.prob_cruce),
                            ("Prob. de mutación", self.prob_mut), ("", self.elitismo),
                            ("Semilla", self.semilla)]:
            self.form.addRow(etiqueta, w)

        self.funcion.currentIndexChanged.connect(lambda _: self._actualizar_info())
        self.n.valueChanged.connect(lambda _: self._actualizar_info())
        self.cruce.currentIndexChanged.connect(lambda _: self._actualizar_info())
        self._actualizar_info()

    def _config(self):
        nombre = self.funcion.currentData()
        return obtener_funcion(nombre, self.n.value() if nombre in CON_N else None)

    def _actualizar_info(self):
        nombre = self.funcion.currentData()
        self.n.setEnabled(nombre in CON_N)
        c = self._config()
        tipo = "Maximizar" if c["tipo"] == "max" else "Minimizar"
        rango = f"[{c['x_min'][0]:g}, {c['x_max'][0]:g}]"
        x_opt = "—" if c["x_opt"] is None else (
            f"{c['x_opt'][0]:g}" if c["n"] == 1 else f"({c['x_opt'][0]:g}, …)")
        self.info(f"<b>{nombre}</b> · {tipo} · n = {c['n']}<br>"
                  f"Intervalo de cada variable: {rango}<br>"
                  f"Óptimo según el libro: <b>{c['optimo']}</b> en x = {x_opt}<br>"
                  f"<span style='color:#9ca3af'>La fórmula aparece arriba de la gráfica.</span>")
        if c["n"] == 1 and self.cruce.currentData() in ("un_punto", "uniforme"):
            self.aviso("Con 1 variable, los cruces de un punto y uniforme no mezclan nada "
                       "(los hijos son copias): solo la mutación mueve a la población. "
                       "Prueba con aritmético o SBX.")
        else:
            self.aviso("")

    def leer_parametros(self):
        nombre = self.funcion.currentData()
        s = self.semilla.value()
        return dict(funcion=nombre, n=self.n.value() if nombre in CON_N else None,
                    cruce=self.cruce.currentData(), tam_pob=self.tam_pob.value(),
                    num_gen=self.num_gen.value(), prob_cruce=self.prob_cruce.value(),
                    prob_mut=self.prob_mut.value(), elitismo=self.elitismo.isChecked(),
                    semilla=None if s < 0 else s)

    def ejecutar(self, p, progreso):
        return correr(p, progreso)


if __name__ == "__main__":
    iniciar(VentanaProyecto2)

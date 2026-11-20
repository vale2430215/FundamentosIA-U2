"""
Graficas del Proyecto 2 (AG con codificacion real).

Genera en la carpeta "graficas/":
  1_comparacion_cruces.png   convergencia de los 4 cruces (media de varias ejecuciones)
  2_cajas_cruces.png         distribucion del resultado final de cada cruce
  3_poblacion_rastrigin.png  como se mueve la poblacion en 2D a lo largo de las generaciones
  4_una_variable.png         las 8 funciones de una variable resueltas con AG real

Ejecutar:  python graficas_proyecto2.py
"""

import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from ag_real import TIPOS_CRUCE, algoritmo_genetico
from funciones import FUNCIONES_MAX, FUNCIONES_MIN, obtener_funcion

matplotlib.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 150, "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "axes.titlesize": 10,
})
AZUL, NARANJA, AQUA, AMARILLO, GRIS = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8a8984"
COLOR_CRUCE = {"un_punto": AZUL, "uniforme": NARANJA, "aritmetico": AQUA, "sbx": AMARILLO}
NOMBRE_CRUCE = {"un_punto": "Un punto", "uniforme": "Discreto uniforme",
                "aritmetico": "Aritmético", "sbx": "SBX"}
CARPETA = "graficas"
os.makedirs(CARPETA, exist_ok=True)

PARAM = dict(tam_pob=100, num_gen=300, prob_cruce=0.6, prob_mut=0.05)
CASOS = [("rastrigin", 10), ("michalewicz", 5), ("schwefel", 10), ("schaffer", None)]
EJECUCIONES = 10


def correr_todos():
    """Ejecuta cada cruce en cada funcion varias veces y guarda los historiales."""
    datos = {}
    for nombre, n in CASOS:
        c = obtener_funcion(nombre, n)
        for cruce in TIPOS_CRUCE:
            hist = [algoritmo_genetico(c, tipo_cruce=cruce, semilla=500 + s, **PARAM)
                    ["hist_mejor_absoluto"] for s in range(EJECUCIONES)]
            datos[(nombre, cruce)] = np.array(hist)
            print(f"  {nombre:12s} {cruce:11s} final medio = {datos[(nombre, cruce)][:, -1].mean():.5f}")
    return datos


def figura_convergencia(datos):
    fig, axes = plt.subplots(1, len(CASOS), figsize=(16, 4))
    for ax, (nombre, n) in zip(axes, CASOS):
        c = obtener_funcion(nombre, n)
        for cruce in TIPOS_CRUCE:
            h = datos[(nombre, cruce)]
            media = h.mean(axis=0)
            ax.plot(media, color=COLOR_CRUCE[cruce], lw=2, label=NOMBRE_CRUCE[cruce])
            ax.fill_between(np.arange(h.shape[1]), np.percentile(h, 25, axis=0),
                            np.percentile(h, 75, axis=0), color=COLOR_CRUCE[cruce], alpha=0.12)
        ax.axhline(c["optimo"], color="black", ls="--", lw=0.8, label=f"Óptimo ({c['optimo']:.4g})")
        ax.set_title(f"{nombre} (n={c['n']})")
        ax.set_xlabel("Generación")
        ax.set_ylabel("Mejor f(x) encontrado")
        if c["tipo"] == "max":
            ax.set_ylim(0.95, 1.002)
        if nombre == "rastrigin":
            ax.set_ylim(-1, 30)
    axes[0].legend(fontsize=8)
    fig.suptitle(f"Proyecto 2 - Comparación de operadores de cruce (media de {EJECUCIONES} "
                 f"ejecuciones; banda = cuartiles 25-75 %)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "1_comparacion_cruces.png"))
    plt.close(fig)


def figura_cajas(datos):
    fig, axes = plt.subplots(1, len(CASOS), figsize=(16, 3.8))
    for ax, (nombre, n) in zip(axes, CASOS):
        c = obtener_funcion(nombre, n)
        finales = [datos[(nombre, cr)][:, -1] for cr in TIPOS_CRUCE]
        bp = ax.boxplot(finales, patch_artist=True, widths=0.55,
                        medianprops=dict(color="black"))
        for caja, cr in zip(bp["boxes"], TIPOS_CRUCE):
            caja.set_facecolor(COLOR_CRUCE[cr])
            caja.set_alpha(0.75)
        ax.set_xticks(range(1, 5))
        ax.set_xticklabels([NOMBRE_CRUCE[cr] for cr in TIPOS_CRUCE], rotation=20)
        ax.axhline(c["optimo"], color="black", ls="--", lw=0.8)
        ax.set_title(f"{nombre} (n={c['n']}) - resultado final")
        ax.set_ylabel("Mejor f(x) final")
    fig.suptitle("Distribución del resultado final por tipo de cruce (línea punteada = óptimo)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "2_cajas_cruces.png"))
    plt.close(fig)


def figura_poblacion():
    c = obtener_funcion("rastrigin", 2)
    res = algoritmo_genetico(c, tipo_cruce="sbx", semilla=11, tam_pob=100, num_gen=60,
                             prob_cruce=0.6, prob_mut=0.05)
    g = np.linspace(-5.12, 5.12, 300)
    X, Y = np.meshgrid(g, g)
    Z = 20 + X ** 2 - 10 * np.cos(2 * np.pi * X) + Y ** 2 - 10 * np.cos(2 * np.pi * Y)
    gens = [0, 5, 15, 60]
    fig, axes = plt.subplots(1, len(gens), figsize=(16, 4.8))
    for ax, gen in zip(axes, gens):
        ax.contourf(X, Y, Z, levels=30, cmap="Blues_r")
        p = res["poblaciones"][gen]
        ax.scatter(p[:, 0], p[:, 1], s=14, color=NARANJA, edgecolor="white", lw=0.4)
        ax.set_title(f"Generación {gen} - mejor f = {res['hist_mejor_absoluto'][gen]:.4f}")
        ax.set_xlabel("x1")
        ax.set_ylabel("x2")
        ax.set_aspect("equal")
        ax.grid(False)
    fig.suptitle("Evolución de la población sobre rastrigin (n=2, cruce SBX)", fontsize=12,
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "3_poblacion_rastrigin.png"))
    plt.close(fig)


def figura_una_variable():
    nombres = FUNCIONES_MAX + FUNCIONES_MIN
    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    for ax, nombre in zip(axes.flat, nombres):
        c = obtener_funcion(nombre)
        # con una sola variable, el cruce de un punto y el uniforme no mezclan nada,
        # por eso aqui se usa el aritmetico
        res = algoritmo_genetico(c, tipo_cruce="aritmetico", semilla=3, tam_pob=100,
                                 num_gen=150, prob_cruce=0.6, prob_mut=0.05)
        xs = np.linspace(c["x_min"][0], c["x_max"][0], 4000)
        ys = [c["f"](np.array([x])) for x in xs]
        ax.plot(xs, ys, color=AZUL, lw=1.1)
        ax.plot(res["mejor_x"][0], res["mejor_f"], "o", ms=9, color=NARANJA,
                markeredgecolor="white", markeredgewidth=1.5, zorder=5)
        ax.set_title(f"{nombre}: AG x={res['mejor_x'][0]:.4f}, f={res['mejor_f']:.5f}\n"
                     f"(libro: {c['optimo']} en {c['x_opt'][0]})", fontsize=8.5)
        ax.set_xlabel("x")
    fig.suptitle("Proyecto 2 - Funciones de una variable con AG real (cruce aritmético)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "4_una_variable.png"))
    plt.close(fig)


if __name__ == "__main__":
    print("1-2. Comparación de cruces")
    datos = correr_todos()
    figura_convergencia(datos)
    figura_cajas(datos)
    print("3. Población en 2D")
    figura_poblacion()
    print("4. Funciones de una variable")
    figura_una_variable()
    print(f"Listo. Gráficas guardadas en la carpeta '{CARPETA}/'")

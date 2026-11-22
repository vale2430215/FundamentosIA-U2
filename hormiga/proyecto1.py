"""
Algoritmo genético (maximización) - Proyecto 1, versión en Python.

Función a maximizar:
    f(x) = 20 + e - 20*exp(-0.2*|x|) - exp(cos(2*pi*x)),   x en [0, 32]
    (máximo ~22.3136 cerca de x = 31.5005)

Solo usa numpy y matplotlib (nada de deap ni librerías de AG).
"""
import argparse
import math

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# ----------------------------------------------------------------------
# Función a optimizar
# ----------------------------------------------------------------------
def funcion_objetivo(x):
    """Aquí se especifica la función a maximizar."""
    return 20 + math.e - 20 * np.exp(-0.2 * np.abs(x)) - np.exp(np.cos(2 * np.pi * x))


# ----------------------------------------------------------------------
# Representación: cada individuo es una cadena de bits (genotipo)
# ----------------------------------------------------------------------
def longitud_cromosoma(x_min, x_max, tol):
    """Bits necesarios para representar el intervalo con la tolerancia dada."""
    return int(math.ceil(math.log(1 + (x_max - x_min) / tol) / math.log(2)))


def bin_dec(genes):
    """Convierte binario a decimal. genes[..., 0] es el bit menos significativo."""
    potencias = 2.0 ** np.arange(genes.shape[-1])
    return genes @ potencias


def decod(genes, x_min, x_max):
    """Decodifica genotipo -> fenotipo (valor real de x dentro del intervalo)."""
    lcrom = genes.shape[-1]
    x = bin_dec(genes) / (2.0 ** lcrom - 1)
    return x_min + (x_max - x_min) * x


def adaptacion(genes, x_min, x_max):
    """Aptitud de uno o varios individuos (en este problema, f(x))."""
    return funcion_objetivo(decod(genes, x_min, x_max))


# ----------------------------------------------------------------------
# Operadores del algoritmo genético
# ----------------------------------------------------------------------
def poblacion_inicial(tam_pob, lcrom, rng):
    """Población aleatoria: cada gen es 0 o 1 con probabilidad 50 %."""
    return rng.integers(0, 2, size=(tam_pob, lcrom)).astype(np.int8)


def seleccion(genes, aptitud, rng, pct_elite=2):
    """
    Selección por ruleta con elitismo.
    Los mejores (pct_elite % de la población) sobreviven en su misma posición;
    el resto de posiciones se llenan tirando la ruleta.
    Devuelve la nueva población y una máscara booleana de la élite.
    """
    tam_pob = len(genes)
    tam_elite = max(1, tam_pob * pct_elite // 100)

    # Ruleta: puntuación relativa y puntuación acumulada
    puntuacion = aptitud / aptitud.sum()
    punt_acu = np.cumsum(puntuacion)

    # Para cada individuo se tira un número aleatorio en [0,1) y se busca
    # el primer individuo cuya puntuación acumulada lo supera
    tiradas = rng.random(tam_pob)
    sel = np.searchsorted(punt_acu, tiradas)
    sel = np.minimum(sel, tam_pob - 1)

    # Élite: los mejores se quedan donde están
    pos_elite = np.argsort(aptitud)[-tam_elite:]
    sel[pos_elite] = pos_elite
    elite = np.zeros(tam_pob, dtype=bool)
    elite[pos_elite] = True

    return genes[sel].copy(), elite


def cruce(padre1, padre2, punto):
    """Cruce en un punto: se intercambian las colas de los dos padres."""
    hijo1 = np.concatenate((padre1[:punto], padre2[punto:]))
    hijo2 = np.concatenate((padre2[:punto], padre1[punto:]))
    return hijo1, hijo2


def reproduccion(genes, elite, prob_cruce, x_min, x_max, rng):
    """
    Elige individuos para cruzarse (con probabilidad prob_cruce), los empareja
    y los cruza. CORRECCIÓN respecto al libro: el hijo reemplaza al padre si
    es MEJOR que él, o si el padre no es de la élite.
    """
    tam_pob, lcrom = genes.shape
    aptitud = adaptacion(genes, x_min, x_max)

    # Individuos elegidos para cruzar
    elegidos = np.flatnonzero(rng.random(tam_pob) < prob_cruce)
    if len(elegidos) % 2 == 1:          # el número de elegidos debe ser par
        elegidos = elegidos[:-1]

    for k in range(0, len(elegidos), 2):
        a, b = elegidos[k], elegidos[k + 1]
        punto = rng.integers(1, lcrom)  # punto de cruce entre 1 y lcrom-1
        hijo1, hijo2 = cruce(genes[a], genes[b], punto)

        apt1 = adaptacion(hijo1, x_min, x_max)
        apt2 = adaptacion(hijo2, x_min, x_max)

        if apt1 > aptitud[a] or not elite[a]:
            genes[a] = hijo1
        if apt2 > aptitud[b] or not elite[b]:
            genes[b] = hijo2


def mutacion(genes, elite, prob_mut, rng):
    """Cada gen de un individuo NO élite se invierte con probabilidad prob_mut."""
    mascara = rng.random(genes.shape) < prob_mut
    mascara[elite] = False
    genes ^= mascara.astype(np.int8)


def evaluacion(genes, x_min, x_max):
    """Calcula fenotipos, aptitudes y la posición del mejor individuo."""
    x = decod(genes, x_min, x_max)
    aptitud = funcion_objetivo(x)
    pos_mejor = int(np.argmax(aptitud))
    return x, aptitud, pos_mejor


# ----------------------------------------------------------------------
# Bucle de evolución (guarda el historial para poder animarlo después)
# ----------------------------------------------------------------------
def evolucionar(x_min, x_max, tol, tam_pob, num_gen, prob_cruce, prob_mut, semilla=None):
    rng = np.random.default_rng(semilla)
    lcrom = longitud_cromosoma(x_min, x_max, tol)

    genes = poblacion_inicial(tam_pob, lcrom, rng)
    x, aptitud, pos_mejor = evaluacion(genes, x_min, x_max)

    historial = {"x": [x], "apt": [aptitud],
                 "mejor": [aptitud[pos_mejor]], "media": [aptitud.mean()],
                 "x_mejor": [x[pos_mejor]]}

    for _ in range(num_gen):
        genes, elite = seleccion(genes, aptitud, rng)
        reproduccion(genes, elite, prob_cruce, x_min, x_max, rng)
        mutacion(genes, elite, prob_mut, rng)
        x, aptitud, pos_mejor = evaluacion(genes, x_min, x_max)

        historial["x"].append(x)
        historial["apt"].append(aptitud)
        historial["mejor"].append(aptitud[pos_mejor])
        historial["media"].append(aptitud.mean())
        historial["x_mejor"].append(x[pos_mejor])

    return historial, lcrom


# ----------------------------------------------------------------------
# Animación
# ----------------------------------------------------------------------
def animar(historial, x_min, x_max, paso, guardar=None):
    num_gen = len(historial["mejor"]) - 1
    frames = list(range(0, num_gen + 1, paso))
    if frames[-1] != num_gen:
        frames.append(num_gen)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # --- Panel izquierdo: la función y la población sobre ella ---
    xs = np.linspace(x_min, x_max, 4000)
    ys = funcion_objetivo(xs)
    ax1.plot(xs, ys, color="steelblue", lw=1, label="f(x)")
    pobl = ax1.scatter([], [], s=14, color="orange", alpha=0.6, label="Población")
    mejor_pt, = ax1.plot([], [], "r*", ms=16, label="Mejor individuo")
    ax1.set_xlim(x_min, x_max)
    ax1.set_ylim(ys.min() - 0.5, ys.max() + 1.5)
    ax1.set_xlabel("x")
    ax1.set_ylabel("f(x)")
    ax1.set_title("Población sobre la función")
    ax1.legend(loc="lower left")
    ax1.grid(alpha=0.3)

    # --- Panel derecho: evolución de la aptitud ---
    ax2.axhline(ys.max(), color="gray", ls="--", lw=1,
                label=f"Máximo de la función ({ys.max():.4f})")
    linea_mejor, = ax2.plot([], [], color="red", lw=2, label="Mejor aptitud")
    linea_media, = ax2.plot([], [], color="green", lw=1.5, label="Aptitud media")
    ax2.set_xlim(0, num_gen)
    ax2.set_ylim(min(historial["media"]) - 0.5, ys.max() + 1)
    ax2.set_xlabel("Generación")
    ax2.set_ylabel("Aptitud")
    ax2.set_title("Evolución de la aptitud")
    ax2.legend(loc="lower right")
    ax2.grid(alpha=0.3)

    titulo = fig.suptitle("")

    def actualizar(g):
        pobl.set_offsets(np.c_[historial["x"][g], historial["apt"][g]])
        mejor_pt.set_data([historial["x_mejor"][g]], [historial["mejor"][g]])
        linea_mejor.set_data(range(g + 1), historial["mejor"][: g + 1])
        linea_media.set_data(range(g + 1), historial["media"][: g + 1])
        titulo.set_text(f"Generación {g}/{num_gen}   |   mejor: {historial['mejor'][g]:.4f} "
                        f"en x = {historial['x_mejor'][g]:.4f}")
        return pobl, mejor_pt, linea_mejor, linea_media, titulo

    anim = FuncAnimation(fig, actualizar, frames=frames, interval=80,
                         blit=False, repeat=False)
    fig.tight_layout()

    if guardar:
        anim.save(guardar, fps=12)
        print(f"Animación guardada en {guardar}")
    else:
        plt.show()
    return anim


# ----------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Algoritmo genético (maximización) con animación")
    p.add_argument("--xmin", type=float, default=0.0, help="límite inferior del intervalo")
    p.add_argument("--xmax", type=float, default=32.0, help="límite superior del intervalo")
    p.add_argument("--tol", type=float, default=0.0001, help="tolerancia (exactitud)")
    p.add_argument("--pob", type=int, default=500, help="tamaño de población")
    p.add_argument("--gen", type=int, default=1000, help="número de generaciones")
    p.add_argument("--cruce", type=float, default=0.4, help="tasa de cruce")
    p.add_argument("--mut", type=float, default=0.001, help="tasa de mutación")
    p.add_argument("--semilla", type=int, default=None, help="semilla aleatoria (opcional)")
    p.add_argument("--paso", type=int, default=None,
                   help="mostrar un cuadro cada N generaciones (por defecto, ~120 cuadros)")
    p.add_argument("--guardar", type=str, default=None,
                   help="guardar la animación (ej. evolucion.gif) en lugar de mostrarla")
    a = p.parse_args()

    historial, lcrom = evolucionar(a.xmin, a.xmax, a.tol, a.pob, a.gen,
                                   a.cruce, a.mut, a.semilla)

    print(f"Longitud del cromosoma: {lcrom} bits")
    print(f"Aptitud del mejor = {historial['mejor'][-1]:.4f} "
          f"en x = {historial['x_mejor'][-1]:.4f}")

    paso = a.paso if a.paso else max(1, a.gen // 120)
    animar(historial, a.xmin, a.xmax, paso, a.guardar)


if __name__ == "__main__":
    main()
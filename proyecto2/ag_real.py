"""
PROYECTO 2: OPTIMIZACION DE FUNCIONES (B)
==========================================
Algoritmo genetico con codificacion REAL.
Libro: "Algoritmos Evolutivos: un enfoque practico" (Araujo y Cervigon).

El libro NO trae codigo para este proyecto, solo el enunciado y el
pseudocodigo de los operadores. Este programa es una ampliacion del
Proyecto 1 (misma estructura) cambiando lo que pide el enunciado:

  - Representacion: vector de numeros reales, un gen por variable
                    (ej. [3.24, 2.71, 0.87, 2.34, 4.55])
  - Evaluacion:     f(x) evaluada directamente en el vector de genes
  - Seleccion:      ruleta (con elitismo, como en el Proyecto 1)
  - Cruce:          "un_punto", "uniforme" (discreto uniforme),
                    "aritmetico" o "sbx"
  - Mutacion:       uniforme (un gen se cambia por un valor aleatorio
                    de su intervalo)

No usa DEAP ni ninguna libreria de algoritmos evolutivos.

Uso desde la terminal:
    python ag_real.py <funcion> <tam_pob> <num_gen> <prob_cruce> <prob_mut> <cruce> [n]
Ejemplo:
    python ag_real.py rastrigin 100 300 0.6 0.05 sbx 10
"""

import random
import sys

import numpy as np

from funciones import obtener_funcion

TIPOS_CRUCE = ["un_punto", "uniforme", "aritmetico", "sbx"]


# ---------------------------------------------------------------------------
# Representacion del individuo
#   tipo TGenes = vector de real
# ---------------------------------------------------------------------------
class Individuo:
    def __init__(self, genes=None):
        self.genes = genes            # vector de valores reales (genotipo = fenotipo)
        self.aptitud_bruta = 0.0      # f(x)
        self.aptitud = 0.0            # aptitud revisada (positiva, se maximiza)
        self.puntuacion = 0.0         # puntuacion relativa
        self.punt_acu = 0.0           # puntuacion acumulada
        self.elite = False

    def copia(self):
        nuevo = Individuo(self.genes.copy())
        nuevo.aptitud_bruta = self.aptitud_bruta
        nuevo.aptitud = self.aptitud
        nuevo.puntuacion = self.puntuacion
        nuevo.punt_acu = self.punt_acu
        nuevo.elite = self.elite
        return nuevo


def adaptacion(indiv, f):
    """Funcion de evaluacion: se evalua f directamente sobre los genes."""
    return float(f(indiv.genes))


# ---------------------------------------------------------------------------
# genera_indiv: cada posicion se inicializa con un valor dentro de su rango
#   genes[i] = aleaReal(limiteInf[i], limiteSup[i])
# ---------------------------------------------------------------------------
def genera_indiv(lcrom, x_min, x_max, f):
    genes = np.array([random.uniform(x_min[i], x_max[i]) for i in range(lcrom)])
    indiv = Individuo(genes)
    indiv.aptitud_bruta = adaptacion(indiv, f)
    return indiv


def poblacion_inicial(tam_pob, lcrom, x_min, x_max, f):
    return [genera_indiv(lcrom, x_min, x_max, f) for _ in range(tam_pob)]


# ---------------------------------------------------------------------------
# revisar_adaptacion (igual que en el Proyecto 1)
# ---------------------------------------------------------------------------
def revisar_adaptacion(pob, tipo):
    brutas = [ind.aptitud_bruta for ind in pob]
    if tipo == "min":
        cmax = max(brutas)
        margen = 0.05 * abs(cmax) + 1e-12
        for ind in pob:
            ind.aptitud = cmax + margen - ind.aptitud_bruta
    else:
        cmin = min(brutas)
        desplazamiento = 0.0 if cmin >= 0 else -cmin + 0.05 * abs(cmin)
        for ind in pob:
            ind.aptitud = ind.aptitud_bruta + desplazamiento + 1e-12


def evaluacion(pob):
    sumaptitud = sum(ind.aptitud for ind in pob)
    pos_mejor, aptitud_mejor = 0, -float("inf")
    for i, ind in enumerate(pob):
        if ind.aptitud > aptitud_mejor:
            pos_mejor, aptitud_mejor = i, ind.aptitud
    punt_acu = 0.0
    for ind in pob:
        ind.puntuacion = ind.aptitud / sumaptitud
        ind.punt_acu = ind.puntuacion + punt_acu
        punt_acu += ind.puntuacion
    return pos_mejor, sumaptitud


# ---------------------------------------------------------------------------
# seleccion por RULETA con ELITISMO (2 %)
# ---------------------------------------------------------------------------
def seleccion(pob, elitismo=True):
    tam_pob = len(pob)
    tam_elite = tam_pob * 2 // 100 if elitismo else 0
    for ind in pob:
        ind.elite = False
    if tam_elite > 0:
        orden = sorted(range(tam_pob), key=lambda i: pob[i].aptitud, reverse=True)
        for i in orden[:tam_elite]:
            pob[i].elite = True

    sel_super = []
    for i in range(tam_pob):
        if pob[i].elite:
            sel_super.append(i)
        else:
            prob = random.random()
            pos_super = 0
            while pos_super < tam_pob and prob > pob[pos_super].punt_acu:
                pos_super += 1
            sel_super.append(min(pos_super, tam_pob - 1))
    pob[:] = [pob[i].copia() for i in sel_super]


# ---------------------------------------------------------------------------
# OPERADORES DE CRUCE (seccion 4.2.1 y pseudocodigo del Proyecto 2)
# ---------------------------------------------------------------------------
def cruce_un_punto(p1, p2, lcrom):
    """Cruce discreto de un punto: igual que en el capitulo 2 pero con genes reales.
    Con una sola variable (lcrom = 1) no hay punto de corte y los hijos son copias."""
    if lcrom < 2:
        return p1.copy(), p2.copy()
    punto = random.randint(1, lcrom - 1)
    h1 = np.concatenate([p1[:punto], p2[punto:]])
    h2 = np.concatenate([p2[:punto], p1[punto:]])
    return h1, h2


def cruce_uniforme(p1, p2, lcrom, prob_i=0.5):
    """Cruce discreto uniforme: para cada gen, con probabilidad prob_i
    los hijos heredan los genes intercambiados de los padres."""
    h1, h2 = p1.copy(), p2.copy()
    for i in range(lcrom):
        if random.random() < prob_i:
            h1[i] = p2[i]
            h2[i] = p1[i]
    return h1, h2


def cruce_aritmetico(p1, p2, lcrom, alfa=0.6):
    """Cruce aritmetico:  h_i = alfa * p1_i + (1 - alfa) * p2_i ,  0 <= alfa <= 1"""
    h1 = alfa * p1 + (1 - alfa) * p2
    h2 = alfa * p2 + (1 - alfa) * p1
    return h1, h2


def cruce_sbx(p1, p2, lcrom, n=1):
    """Cruce SBX (binario simulado), con n = 1 como en el libro.
        si alfa < 0.5   beta = (2*alfa)^(1/(n+1))
        si alfa >= 0.5  beta = (1/(2(1-alfa)))^(1/(n+1))
        h1_i = 0.5((p1_i + p2_i) - beta|p2_i - p1_i|)
        h2_i = 0.5((p1_i + p2_i) + beta|p2_i - p1_i|)
    """
    alfa = random.random()
    if alfa < 0.5:
        beta = (2 * alfa) ** (1 / (n + 1))
    else:
        beta = (1 / (2 * (1 - alfa))) ** (1 / (n + 1))
    aux1 = p1 + p2
    aux2 = np.abs(p2 - p1)
    h1 = 0.5 * (aux1 - beta * aux2)
    h2 = 0.5 * (aux1 + beta * aux2)
    return h1, h2


def cruce(padre1, padre2, lcrom, tipo_cruce, x_min, x_max, f):
    p1, p2 = padre1.genes, padre2.genes
    if tipo_cruce == "un_punto":
        g1, g2 = cruce_un_punto(p1, p2, lcrom)
    elif tipo_cruce == "uniforme":
        g1, g2 = cruce_uniforme(p1, p2, lcrom)
    elif tipo_cruce == "aritmetico":
        g1, g2 = cruce_aritmetico(p1, p2, lcrom)
    elif tipo_cruce == "sbx":
        g1, g2 = cruce_sbx(p1, p2, lcrom)
    else:
        raise ValueError(f"Cruce desconocido: {tipo_cruce}")
    # SBX puede generar valores fuera del intervalo: se recortan al rango permitido
    g1 = np.clip(g1, x_min, x_max)
    g2 = np.clip(g2, x_min, x_max)
    hijo1, hijo2 = Individuo(g1), Individuo(g2)
    hijo1.aptitud_bruta = adaptacion(hijo1, f)
    hijo2.aptitud_bruta = adaptacion(hijo2, f)
    return hijo1, hijo2


def es_mejor(a, b, tipo):
    return a > b if tipo == "max" else a < b


def reproduccion(pob, prob_cruce, lcrom, tipo_cruce, x_min, x_max, f, tipo):
    sel_cruce = [i for i in range(len(pob)) if random.random() < prob_cruce]
    if len(sel_cruce) % 2 == 1:
        sel_cruce.pop()
    for k in range(0, len(sel_cruce), 2):
        i1, i2 = sel_cruce[k], sel_cruce[k + 1]
        hijo1, hijo2 = cruce(pob[i1], pob[i2], lcrom, tipo_cruce, x_min, x_max, f)
        if not pob[i1].elite or es_mejor(hijo1.aptitud_bruta, pob[i1].aptitud_bruta, tipo):
            pob[i1] = hijo1
        if not pob[i2].elite or es_mejor(hijo2.aptitud_bruta, pob[i2].aptitud_bruta, tipo):
            pob[i2] = hijo2


# ---------------------------------------------------------------------------
# MUTACION UNIFORME: el gen se sustituye por un valor aleatorio valido
#   pob[i].genes[j] = aleaReal(inf[j], sup[j])
# ---------------------------------------------------------------------------
def mutacion(pob, prob_mut, lcrom, x_min, x_max, f):
    for ind in pob:
        if ind.elite:
            continue
        mutado = False
        for j in range(lcrom):
            if random.random() < prob_mut:
                ind.genes[j] = random.uniform(x_min[j], x_max[j])
                mutado = True
        if mutado:
            ind.aptitud_bruta = adaptacion(ind, f)


# ---------------------------------------------------------------------------
# ALGORITMO GENETICO
# ---------------------------------------------------------------------------
def algoritmo_genetico(config, tam_pob=100, num_gen=100, prob_cruce=0.6, prob_mut=0.05,
                       tipo_cruce="sbx", elitismo=True, semilla=None, verbose=False,
                       progreso=None):
    """progreso (opcional): funcion que recibe la fraccion completada (0 a 1);
    la usa el visualizador para su barra de progreso."""
    if semilla is not None:
        random.seed(semilla)
        np.random.seed(semilla)

    f, tipo = config["f"], config["tipo"]
    x_min = np.array(config["x_min"], dtype=float)
    x_max = np.array(config["x_max"], dtype=float)
    lcrom = config["n"]  # un gen por variable

    pob = poblacion_inicial(tam_pob, lcrom, x_min, x_max, f)
    revisar_adaptacion(pob, tipo)
    pos_mejor, _ = evaluacion(pob)

    hist_mejor, hist_media, hist_abs = [], [], []
    poblaciones = {}
    mejor_global = pob[pos_mejor].copia()

    def registrar(gen):
        nonlocal mejor_global
        mejor = pob[pos_mejor]
        if gen == 0 or es_mejor(mejor.aptitud_bruta, mejor_global.aptitud_bruta, tipo):
            mejor_global = mejor.copia()
        hist_mejor.append(mejor.aptitud_bruta)
        hist_media.append(float(np.mean([ind.aptitud_bruta for ind in pob])))
        hist_abs.append(mejor_global.aptitud_bruta)
        poblaciones[gen] = np.array([ind.genes for ind in pob])

    registrar(0)
    for generacion in range(1, num_gen + 1):
        seleccion(pob, elitismo)
        reproduccion(pob, prob_cruce, lcrom, tipo_cruce, x_min, x_max, f, tipo)
        mutacion(pob, prob_mut, lcrom, x_min, x_max, f)
        revisar_adaptacion(pob, tipo)
        pos_mejor, _ = evaluacion(pob)
        registrar(generacion)
        if progreso is not None:
            progreso(generacion / num_gen)
        if verbose and generacion % max(1, num_gen // 10) == 0:
            print(f"  gen {generacion:5d}  mejor = {hist_abs[-1]:.6f}")

    return dict(mejor_x=list(mejor_global.genes), mejor_f=mejor_global.aptitud_bruta,
                hist_mejor=hist_mejor, hist_media=hist_media,
                hist_mejor_absoluto=hist_abs, poblaciones=poblaciones)


if __name__ == "__main__":
    if len(sys.argv) < 7:
        print(__doc__)
        print("Funciones: max1..max4, min1..min4, schaffer, rastrigin, michalewicz, schwefel")
        print("Cruces:", ", ".join(TIPOS_CRUCE))
        sys.exit(0)

    nombre = sys.argv[1]
    tam_pob = int(sys.argv[2])
    num_gen = int(sys.argv[3])
    prob_cruce = float(sys.argv[4])
    prob_mut = float(sys.argv[5])
    tipo_cruce = sys.argv[6]
    n = int(sys.argv[7]) if len(sys.argv) > 7 else None

    config = obtener_funcion(nombre, n)
    res = algoritmo_genetico(config, tam_pob, num_gen, prob_cruce, prob_mut, tipo_cruce,
                             verbose=True)
    xs = ", ".join(f"{v:.6f}" for v in res["mejor_x"])
    print(f"\nFuncion: {nombre}  cruce: {tipo_cruce}")
    print(f"Mejor = {res['mejor_f']:.6f}  en  x = [{xs}]")
    print(f"Optimo segun el libro = {config['optimo']}")

    import matplotlib.pyplot as plt
    plt.plot(res["hist_mejor_absoluto"], label="Mejor absoluto")
    plt.plot(res["hist_mejor"], label="Mejor de la generacion", alpha=0.7)
    plt.plot(res["hist_media"], label="Media de la generacion", alpha=0.7)
    plt.xlabel("Generacion")
    plt.ylabel("f(x)")
    plt.title(f"Evolucion - {nombre} (cruce {tipo_cruce})")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

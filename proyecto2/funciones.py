"""
funciones.py
------------
Funciones de prueba de los Proyectos 1 y 2 del libro
"Algoritmos Evolutivos: un enfoque practico" (Araujo y Cervigon).

Cada funcion se describe con un diccionario:
    f        -> la funcion; recibe un vector numpy x (una entrada por variable)
    tipo     -> "max" o "min"
    x_min    -> limite inferior de cada variable
    x_max    -> limite superior de cada variable
    n        -> numero de variables
    optimo   -> valor optimo que reporta el libro (para comparar)
    x_opt    -> punto donde esta el optimo (segun el libro)
    texto    -> formula para mostrar en las graficas
"""

import numpy as np

PI = np.pi
E = np.e


# ---------------------------------------------------------------------------
# 1. MAXIMIZACION (una variable)
# ---------------------------------------------------------------------------
def max1(x):
    x = x[0]
    return np.sin(5 * PI * x) ** 6 * np.exp(-2 * np.log(2) * ((x - 0.1) / 0.8) ** 2)


def max2(x):
    # Es la funcion que usa el codigo C++ del Apendice B
    x = x[0]
    return 20 + E - 20 * np.exp(-0.2 * abs(x)) - np.exp(np.cos(2 * PI * x))


def max3(x):
    x = x[0]
    return x + abs(np.sin(32 * PI * x))


def max4(x):
    x = x[0]
    return 0.5 - (np.sin(x) ** 2 - 0.5) / (1 + 0.001 * x ** 4)


# ---------------------------------------------------------------------------
# 2. MINIMIZACION (una variable)
# ---------------------------------------------------------------------------
def min1(x):
    x = x[0]
    return 1 + np.cos(x) / (1 + 0.01 * x ** 2)


def min2(x):
    # Es la funcion que usa el codigo C++ "Funciones.cpp para minimizar"
    x = x[0]
    return -abs(x * np.sin(np.sqrt(abs(x))))


def min3(x):
    x = x[0]
    return np.sin(x) / (1 + np.sqrt(x) + np.cos(x) / (1 + x))


def min4(x):
    # OJO: en el libro esta impresa como 5 + exp(0.5(pi x^2)) - exp(0.1 x cos(pi x)),
    # pero asi la funcion explota y su minimo NO es -5.39204.
    # La version correcta (falta un "sen") es la siguiente, que si da
    # el minimo -5.39204 en x = 23.9901 que reporta el libro.
    x = x[0]
    return 5 + np.exp(0.5 * np.sin(PI * x ** 2)) - np.exp(0.1 * x * np.cos(PI * x))


# ---------------------------------------------------------------------------
# 3. VARIAS VARIABLES
# ---------------------------------------------------------------------------
def schaffer(x):
    # f(x1,x2) = 0.5 - (sen(sqrt(x1^2+x2^2))^2 - 0.5) / (1 + 0.001(x1^2+x2^2))^2
    r2 = x[0] ** 2 + x[1] ** 2
    return 0.5 - (np.sin(np.sqrt(r2)) ** 2 - 0.5) / (1.0 + 0.001 * r2) ** 2


def rastrigin(x):
    # f = 10n + sum(x_i^2 - 10 cos(2 pi x_i))
    n = len(x)
    return 10 * n + np.sum(x ** 2 - 10 * np.cos(2 * PI * x))


def michalewicz(x):
    # f = -sum sen(x_i) * sen^20((i+1) x_i^2 / pi),  i = 1..n
    i = np.arange(1, len(x) + 1)
    return -np.sum(np.sin(x) * np.sin((i + 1) * x ** 2 / PI) ** 20)


def schwefel(x):
    # f = sum(-x_i * sen(sqrt(|x_i|)))   (es la del codigo C++ "varias variables")
    return np.sum(-x * np.sin(np.sqrt(np.abs(x))))


# Minimos de michalewicz segun la tabla del libro
TABLA_MICHALEWICZ = {1: -1, 2: -1.959091, 3: -2.897553, 4: -3.886358, 5: -4.886358,
                     6: -5.879585, 7: -6.862457, 8: -7.858851, 9: -8.858851, 10: -9.856182}


def obtener_funcion(nombre, n=None):
    """Devuelve el diccionario de configuracion de una funcion por su nombre."""
    if nombre == "max1":
        return dict(nombre=nombre, f=max1, tipo="max", x_min=[0.0], x_max=[1.0], n=1,
                    optimo=1.0, x_opt=[0.1],
                    texto=r"$f(x)=\sin^6(5\pi x)\,e^{-2\ln 2\,((x-0.1)/0.8)^2}$")
    if nombre == "max2":
        return dict(nombre=nombre, f=max2, tipo="max", x_min=[0.0], x_max=[32.0], n=1,
                    optimo=22.3136, x_opt=[31.5005],
                    texto=r"$f(x)=20+e-20e^{-0.2|x|}-e^{\cos 2\pi x}$")
    if nombre == "max3":
        return dict(nombre=nombre, f=max3, tipo="max", x_min=[0.0], x_max=[1.0], n=1,
                    optimo=1.98442447, x_opt=[0.98447395],
                    texto=r"$f(x)=x+|\sin(32\pi x)|$")
    if nombre == "max4":
        return dict(nombre=nombre, f=max4, tipo="max", x_min=[0.0], x_max=[10.0], n=1,
                    optimo=1.0, x_opt=[0.0],
                    texto=r"$f(x)=0.5-\frac{\sin^2 x-0.5}{1+0.001x^4}$")
    if nombre == "min1":
        return dict(nombre=nombre, f=min1, tipo="min", x_min=[0.0], x_max=[50.0], n=1,
                    optimo=0.0883634, x_opt=[3.08531],
                    texto=r"$f(x)=1+\frac{\cos x}{1+0.01x^2}$")
    if nombre == "min2":
        return dict(nombre=nombre, f=min2, tipo="min", x_min=[-250.0], x_max=[250.0], n=1,
                    optimo=-201.843, x_opt=[203.814],
                    texto=r"$f(x)=-|x\,\sin(\sqrt{|x|})|$")
    if nombre == "min3":
        return dict(nombre=nombre, f=min3, tipo="min", x_min=[0.0], x_max=[25.0], n=1,
                    optimo=-0.318071, x_opt=[4.5798],
                    texto=r"$f(x)=\frac{\sin x}{1+\sqrt{x}+\frac{\cos x}{1+x}}$")
    if nombre == "min4":
        return dict(nombre=nombre, f=min4, tipo="min", x_min=[0.0], x_max=[25.0], n=1,
                    optimo=-5.39204, x_opt=[23.9901],
                    texto=r"$f(x)=5+e^{0.5\sin(\pi x^2)}-e^{0.1x\cos(\pi x)}$")
    if nombre == "schaffer":
        return dict(nombre=nombre, f=schaffer, tipo="max", x_min=[-40.0] * 2, x_max=[40.0] * 2,
                    n=2, optimo=1.0, x_opt=[0.0, 0.0],
                    texto=r"$f(x_1,x_2)=0.5-\frac{\sin^2\sqrt{x_1^2+x_2^2}-0.5}{(1+0.001(x_1^2+x_2^2))^2}$")
    if nombre == "rastrigin":
        n = n or 2
        return dict(nombre=nombre, f=rastrigin, tipo="min", x_min=[-5.12] * n, x_max=[5.12] * n,
                    n=n, optimo=0.0, x_opt=[0.0] * n,
                    texto=rf"$f=10n+\sum(x_i^2-10\cos 2\pi x_i)$, n={n}")
    if nombre == "michalewicz":
        n = n or 2
        return dict(nombre=nombre, f=michalewicz, tipo="min", x_min=[0.0] * n, x_max=[PI] * n,
                    n=n, optimo=TABLA_MICHALEWICZ.get(n), x_opt=None,
                    texto=rf"$f=-\sum\sin(x_i)\sin^{{20}}((i+1)x_i^2/\pi)$, n={n}")
    if nombre == "schwefel":
        n = n or 2
        return dict(nombre=nombre, f=schwefel, tipo="min", x_min=[0.0] * n, x_max=[100.0] * n,
                    n=n, optimo=-n * 63.63498, x_opt=[65.54785] * n,
                    texto=rf"$f=\sum -x_i\sin(\sqrt{{|x_i|}})$, n={n}")
    raise ValueError(f"Funcion desconocida: {nombre}")


FUNCIONES_MAX = ["max1", "max2", "max3", "max4"]
FUNCIONES_MIN = ["min1", "min2", "min3", "min4"]
FUNCIONES_VARIAS = ["schaffer", "rastrigin", "michalewicz", "schwefel"]
TODAS = FUNCIONES_MAX + FUNCIONES_MIN + FUNCIONES_VARIAS

"""Muestreo de una función para graficarla (Python puro, sin numpy).

`muestrear(f, xmin, xmax, n)` evalúa f punto por punto y devuelve una `Muestra`:

* xs / ys        serie lista para dibujar; los huecos se marcan con NaN para que la
                 línea se corte donde la función no está definida o tiene una asíntota
* indefinidos    intervalos donde no hay valores reales (con su motivo)
* asintotas      posiciones aproximadas de asíntotas verticales
* ymin / ymax    límites verticales razonables (recortan las asíntotas)

Detalles que se cuidan:

* Frontera del dominio: cuando se pasa de "definido" a "no definido" se busca el borde
  por bisección, de modo que la curva llega justo hasta, p. ej., x = -3 en
  sqrt(2x^2+5x-3), en lugar de quedarse a medio paso.
* Asíntotas: un cambio de signo con módulos que crecen hacia el salto (como 1/x o
  tan x) corta la línea; un cruce de cero normal, aunque sea empinado, no.
* División entre cero en un punto aislado: si la curva sigue de forma continua
  (sin(x)/x en x = 0) se deja conectada y se avisa como discontinuidad evitable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from .errors import DivisionCeroError, EvaluacionError

NAN = float("nan")


def _fmt(x: float) -> str:
    return f"{x:.6g}"


@dataclass
class IntervaloIndefinido:
    inicio: float
    fin: float
    motivo: str
    tipo: str                      # 'dom' (fuera de dominio) | 'div' (división entre cero)
    abierto_izq: bool = False      # el extremo pertenece al dominio (está definido)
    abierto_der: bool = False
    evitable: bool = False         # discontinuidad evitable (solo 'div' puntual)

    @property
    def puntual(self) -> bool:
        return self.inicio == self.fin

    def rango(self) -> str:
        if self.puntual:
            return _fmt(self.inicio)
        izq = "(" if self.abierto_izq else "["
        der = ")" if self.abierto_der else "]"
        return f"{izq}{_fmt(self.inicio)}, {_fmt(self.fin)}{der}"

    def descripcion(self) -> str:
        if self.tipo == "div":
            if self.puntual:
                extra = (" (discontinuidad evitable: la curva continúa)"
                         if self.evitable else "")
                return f"División entre cero en x = {_fmt(self.inicio)}{extra}."
            return f"División entre cero en x ∈ {self.rango()}."
        return f"Sin valores reales en x ∈ {self.rango()}: {self.motivo}."


@dataclass
class Muestra:
    xs: list[float]
    ys: list[float]                # NaN = corte de línea
    asintotas: list[float]
    indefinidos: list[IntervaloIndefinido]
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    n_validos: int
    n_total: int

    def resumen(self) -> list[str]:
        """Descripción legible del dominio y las asíntotas."""
        if self.n_validos == 0:
            motivo = self.indefinidos[0].motivo if self.indefinidos else "sin valores"
            return [f"La expresión no toma valores reales en [{_fmt(self.xmin)}, "
                    f"{_fmt(self.xmax)}]: {motivo}."]
        lineas = []
        if not self.indefinidos and not self.asintotas:
            lineas.append("Definida (valores reales) en todo el intervalo.")
        lineas.extend(iv.descripcion() for iv in self.indefinidos)
        if self.asintotas:
            mostrar = ", ".join(f"{a:.4g}" for a in self.asintotas[:8])
            if len(self.asintotas) > 8:
                mostrar += ", …"
            lineas.append(f"Asíntotas verticales (aprox.) en x ≈ {mostrar}.")
        return lineas


# ---------------------------------------------------------------------------
@dataclass
class _Pt:
    x: float
    y: float | None
    tipo: str                      # 'ok' | 'dom' | 'div'
    motivo: str | None = None
    evitable: bool = False


def _evaluar_punto(f: Callable[[float], float], x: float) -> _Pt:
    try:
        return _Pt(x, f(x), "ok")
    except DivisionCeroError as e:
        return _Pt(x, None, "div", e.motivo)
    except EvaluacionError as e:
        return _Pt(x, None, "dom", e.motivo)


def _borde(f: Callable[[float], float], x_def: float, x_indef: float) -> _Pt | None:
    """Bisección: punto definido más cercano posible a la frontera del dominio."""
    a, b = x_def, x_indef
    try:
        ya = f(a)
    except EvaluacionError:
        return None
    for _ in range(60):
        m = (a + b) / 2
        if m == a or m == b:
            break
        try:
            ym = f(m)
        except EvaluacionError:
            b = m
        else:
            a, ya = m, ym
    if a == x_def:
        return None
    return _Pt(a, ya, "ok")


def _limpiar(x: float, escala: float) -> float:
    """La bisección deja residuos tipo 6.5e-21 en lugar de 0: se redondean a 0."""
    return 0.0 if abs(x) < 1e-9 * escala else x


def _salto_asintotico(y_ant: float | None, y0: float, y1: float,
                      y_sig: float | None) -> bool:
    """¿Entre y0 e y1 hay una asíntota vertical (y no un simple cruce por cero)?"""
    if y0 * y1 >= 0:
        return False
    vecinos = [abs(v) for v in (y_ant, y_sig) if v is not None]
    if not vecinos:
        return False
    if y_ant is not None and abs(y0) <= abs(y_ant):
        return False                         # se acerca a cero por la izquierda
    if y_sig is not None and abs(y1) <= abs(y_sig):
        return False                         # se aleja de cero por la derecha
    return abs(y1 - y0) > 3 * max(vecinos)


def _crece(y_lejos: float | None, y_cerca: float) -> bool:
    """¿El módulo crece claramente al acercarse a un punto indefinido?"""
    return y_lejos is not None and abs(y_cerca) > 1.5 * abs(y_lejos)


def _limites_y(valores: list[float]) -> tuple[float, float]:
    if not valores:
        return -1.0, 1.0
    v = sorted(valores)
    n = len(v)
    lo, hi = v[0], v[-1]
    p_lo, p_hi = v[int(0.02 * (n - 1))], v[int(0.98 * (n - 1))]
    span_p = p_hi - p_lo
    if span_p > 0 and (hi - lo) > 5 * span_p:      # colas enormes (asíntotas): recortar
        lo, hi = p_lo - 0.5 * span_p, p_hi + 0.5 * span_p
    span = hi - lo
    if span == 0:                                  # función constante
        return lo - 1.0, hi + 1.0
    pad = 0.06 * span
    return lo - pad, hi + pad


# ---------------------------------------------------------------------------
def muestrear(f: Callable[[float], float], xmin: float, xmax: float,
              n: int = 800, refinar: bool = True) -> Muestra:
    """Evalúa `f` en `n` puntos equiespaciados de [xmin, xmax]."""
    if not (math.isfinite(xmin) and math.isfinite(xmax)):
        raise ValueError("Los límites del intervalo deben ser números finitos")
    if xmin >= xmax:
        raise ValueError("El límite inferior debe ser menor que el superior")
    if n < 2:
        raise ValueError("Se necesitan al menos 2 puntos")

    paso = (xmax - xmin) / (n - 1)
    crudos = [_evaluar_punto(f, xmax if i == n - 1 else xmin + i * paso)
              for i in range(n)]

    # 1) refinar las fronteras del dominio por bisección
    pts: list[_Pt] = []
    for i, p in enumerate(crudos):
        if refinar and i > 0:
            q = crudos[i - 1]
            borde = None
            if q.tipo == "ok" and p.tipo == "dom":
                borde = _borde(f, q.x, p.x)
            elif q.tipo == "dom" and p.tipo == "ok":
                borde = _borde(f, p.x, q.x)
            if borde is not None:
                pts.append(borde)
        pts.append(p)

    def y_de(k: int) -> float | None:
        return pts[k].y if 0 <= k < len(pts) and pts[k].tipo == "ok" else None

    # 2) construir la serie con cortes (NaN) en huecos y asíntotas
    xs: list[float] = []
    ys: list[float] = []
    asintotas: list[float] = []
    for i, p in enumerate(pts):
        if p.tipo != "ok":
            corta = True
            if p.tipo == "div":
                izq_ok = i > 0 and pts[i - 1].tipo == "ok"
                der_ok = i + 1 < len(pts) and pts[i + 1].tipo == "ok"
                aislado = (i == 0 or pts[i - 1].tipo != "div") and \
                          (i + 1 >= len(pts) or pts[i + 1].tipo != "div")
                if izq_ok and der_ok:
                    if _crece(y_de(i - 2), y_de(i - 1)) or _crece(y_de(i + 2), y_de(i + 1)):
                        asintotas.append(p.x)
                    else:
                        p.evitable = True           # la curva continúa: no cortar
                        corta = False
                elif aislado:
                    asintotas.append(p.x)
            if corta and (not ys or not math.isnan(ys[-1])):
                xs.append(p.x)
                ys.append(NAN)
            continue

        if ys and not math.isnan(ys[-1]) and pts[i - 1].tipo == "ok":
            ant = pts[i - 1]                         # punto anterior contiguo y definido
            if _salto_asintotico(y_de(i - 2), ant.y, p.y, y_de(i + 1)):
                medio = (ant.x + p.x) / 2
                asintotas.append(medio)
                xs.append(medio)
                ys.append(NAN)
        xs.append(p.x)
        ys.append(p.y)

    # 3) intervalos sin valores reales
    indefinidos: list[IntervaloIndefinido] = []
    i = 0
    while i < len(pts):
        p = pts[i]
        if p.tipo == "ok":
            i += 1
            continue
        j = i
        while j + 1 < len(pts) and pts[j + 1].tipo == p.tipo and pts[j + 1].motivo == p.motivo:
            j += 1
        ini, fin = pts[i].x, pts[j].x
        ab_izq = ab_der = False
        if p.tipo == "dom":
            if i > 0 and pts[i - 1].tipo == "ok":
                ini, ab_izq = _limpiar(pts[i - 1].x, xmax - xmin), True
            if j + 1 < len(pts) and pts[j + 1].tipo == "ok":
                fin, ab_der = _limpiar(pts[j + 1].x, xmax - xmin), True
        indefinidos.append(IntervaloIndefinido(
            ini, fin, p.motivo or "", p.tipo, ab_izq, ab_der,
            evitable=(p.tipo == "div" and i == j and p.evitable)))
        i = j + 1

    validos = [y for y in ys if not math.isnan(y)]
    ymin, ymax = _limites_y(validos)
    return Muestra(
        xs=xs, ys=ys, asintotas=sorted(set(asintotas)), indefinidos=indefinidos,
        xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
        n_validos=sum(1 for p in crudos if p.tipo == "ok"), n_total=n,
    )

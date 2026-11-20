"""Métricas de error entre valores exactos y valores representados en el CSV.

Opción A: yᵢ = valor exacto de la función evaluada; ŷᵢ = valor leído del CSV
(con truncado de decimales).  Así se mide el error de representación numérica
introducido al guardar el archivo.

Fórmulas
--------
MSE  = (1/n) · Σ(yᵢ − ŷᵢ)²
RMSE = √MSE
NMSE = 10 · log₁₀( Σ|yᵢ|² / Σ|ŷᵢ|² )     (en dB; compara energías de señal)
R²   = 1 − Σ(yᵢ−ŷᵢ)² / Σ(yᵢ−ȳ)²
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Metricas:
    mse: float
    rmse: float
    nmse_db: float          # NMSE en decibeles (10·log₁₀)
    r2: float
    n: int                  # número de puntos comparados

    def lineas(self) -> list[str]:
        """Representación legible para mostrar en la interfaz."""
        return [
            f"── Métricas de error (exacto vs. CSV, n={self.n}) ──",
            f"  MSE   = {self.mse:.6e}",
            f"  RMSE  = {self.rmse:.6e}",
            f"  NMSE  = {self.nmse_db:.4f} dB",
            f"  R²    = {self.r2:.10f}",
        ]


def calcular(ys_exacto: list[float], ys_csv: list[float]) -> Metricas:
    """Calcula las cuatro métricas entre dos listas del mismo largo.

    Parameters
    ----------
    ys_exacto:
        Valores calculados con precisión de punto flotante doble directamente
        desde la función (sin pasar por el CSV).
    ys_csv:
        Valores leídos de vuelta desde el CSV (suelen tener menos decimales).
    """
    n = len(ys_exacto)
    if n == 0:
        raise ValueError("No hay puntos válidos para calcular las métricas.")
    if len(ys_csv) != n:
        raise ValueError("Las listas deben tener el mismo número de elementos.")

    # MSE y RMSE
    suma_sq_err = sum((y - yh) ** 2 for y, yh in zip(ys_exacto, ys_csv))
    mse = suma_sq_err / n
    rmse = math.sqrt(mse)

    # NMSE  (evitar log(0): si ambas señales son idénticas, NMSE = -inf dB)
    energia_exacto = sum(abs(y) ** 2 for y in ys_exacto)
    energia_csv = sum(abs(yh) ** 2 for yh in ys_csv)
    if energia_csv == 0:
        nmse_db = float("inf")
    elif energia_exacto == 0:
        nmse_db = float("-inf")
    else:
        nmse_db = 10.0 * math.log10(energia_exacto / energia_csv)

    # R²
    media_y = sum(ys_exacto) / n
    ss_tot = sum((y - media_y) ** 2 for y in ys_exacto)
    r2 = 1.0 - (suma_sq_err / ss_tot) if ss_tot != 0 else 1.0

    return Metricas(mse=mse, rmse=rmse, nmse_db=nmse_db, r2=r2, n=n)

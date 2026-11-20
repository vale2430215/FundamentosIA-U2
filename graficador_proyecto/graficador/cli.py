"""Modo consola: imprime el árbol y exporta la figura (PNG) o la animación (GIF).

    python -m graficador cli "sqrt(2*(x^2)+5*x-3)" --png salida.png
    python -m graficador cli "1/x" --xmin -5 --xmax 5 --gif animacion.gif
"""

from __future__ import annotations

import argparse
import math
import sys

from .errors import ExpresionError
from .funcion import Funcion, evaluar_constante


def _crear_figura(f: Funcion, muestra, figsize):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    from .plotting import GraficaPorPuntos
    from .tree_draw import dibujar_arbol

    fig = Figure(figsize=figsize, constrained_layout=True)
    FigureCanvasAgg(fig)
    ax_arbol, ax_graf = fig.subplots(1, 2, gridspec_kw={"width_ratios": [1.1, 1]})
    dibujar_arbol(f.arbol, ax_arbol)
    anim = GraficaPorPuntos(ax_graf, muestra, f"y = {f.texto.strip()}", f.variable)
    return fig, anim


def guardar_png(f: Funcion, muestra, ruta: str) -> None:
    fig, anim = _crear_figura(f, muestra, (14, 6))
    anim.terminar()
    fig.savefig(ruta, dpi=150)


def guardar_gif(f: Funcion, muestra, ruta: str, cuadros: int = 45) -> None:
    from PIL import Image

    fig, anim = _crear_figura(f, muestra, (11, 4.8))
    paso = max(1, math.ceil(anim.total / cuadros))
    imagenes = []
    terminada = False
    while not terminada:
        terminada = anim.avanzar(paso)
        fig.canvas.draw()
        ancho, alto = fig.canvas.get_width_height()
        img = Image.frombuffer("RGBA", (ancho, alto), bytes(fig.canvas.buffer_rgba()),
                               "raw", "RGBA", 0, 1)
        imagenes.append(img.convert("RGB"))
    duraciones = [60] * (len(imagenes) - 1) + [1500]
    imagenes[0].save(ruta, save_all=True, append_images=imagenes[1:],
                     duration=duraciones, loop=0)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m graficador cli",
                                 description="Árbol de expresión y gráfica desde la consola.")
    ap.add_argument("expresion", help='Ej.: "sqrt(2*(x^2)+5*x-3)"')
    ap.add_argument("--xmin", default="-10",
                    help="límite inferior; acepta expresiones (pi, sqrt(2)...). "
                         "Si empieza con '-' usa el signo igual: --xmin=-4*pi")
    ap.add_argument("--xmax", default="10", help="límite superior")
    ap.add_argument("--puntos", type=int, default=800)
    ap.add_argument("--png", metavar="ARCHIVO", help="guarda árbol + gráfica completa")
    ap.add_argument("--gif", metavar="ARCHIVO", help="guarda la animación punto por punto")
    args = ap.parse_args(argv)

    try:
        f = Funcion(args.expresion)
        xmin, xmax = evaluar_constante(args.xmin), evaluar_constante(args.xmax)
        muestra = f.muestrear(xmin, xmax, args.puntos)
    except (ExpresionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print("Árbol de expresión:")
    print(f.arbol_ascii())
    print(f"\nForma parentizada: {f.forma_parentizada()}")
    print("\n" + "\n".join(muestra.resumen()))

    if args.png:
        guardar_png(f, muestra, args.png)
        print(f"\nFigura guardada en: {args.png}")
    if args.gif:
        guardar_gif(f, muestra, args.gif)
        print(f"Animación guardada en: {args.gif}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

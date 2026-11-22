"""Punto de entrada:  python -m graficador   (interfaz)  |  python -m graficador cli ..."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "cli":
        from .cli import main as cli_main
        return cli_main(argv[1:])
    try:
        from .gui import main as gui_main
    except ImportError as e:            # tkinter no instalado (algunas distribuciones Linux)
        print(f"No se pudo abrir la interfaz gráfica: {e}\n"
              "En Debian/Ubuntu: sudo apt install python3-tk\n"
              "Mientras tanto puedes usar el modo consola: python -m graficador cli \"x^2\" --png a.png",
              file=sys.stderr)
        return 1
    gui_main()
    return 0


if __name__ == "__main__":
    sys.exit(main())

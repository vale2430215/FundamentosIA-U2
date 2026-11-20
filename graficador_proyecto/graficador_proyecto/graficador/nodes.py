"""Nodos del árbol de expresión."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Nodo:
    tipo: str                       # 'num', 'var', 'const', 'bin', 'neg', 'func'
    valor: object                   # número, nombre de variable/constante/función u operador
    hijos: list["Nodo"] = field(default_factory=list)

    @property
    def etiqueta(self) -> str:
        """Texto que se muestra en el árbol."""
        if self.tipo == "num":
            v = float(self.valor)
            if v.is_integer() and abs(v) < 1e15:
                return str(int(v))
            return f"{v:g}"
        if self.tipo == "neg":
            return "-(unario)"
        if self.tipo == "func":
            return f"{self.valor}()"
        if self.tipo == "func2":
            return f"{self.valor}(,)"
        return str(self.valor)


def recorrer(nodo: Nodo) -> Iterator[Nodo]:
    """Recorrido en preorden de todos los nodos."""
    yield nodo
    for h in nodo.hijos:
        yield from recorrer(h)


def variables(nodo: Nodo) -> set[str]:
    """Nombres de las variables que aparecen en el árbol."""
    return {n.valor for n in recorrer(nodo) if n.tipo == "var"}


def contar_hojas(nodo: Nodo) -> int:
    if not nodo.hijos:
        return 1
    return sum(contar_hojas(h) for h in nodo.hijos)

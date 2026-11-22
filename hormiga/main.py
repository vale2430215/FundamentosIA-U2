"""
Proyecto: Hormiga buscadora (BFS / DFS) con PyQt, generado por un equipo de agentes CrewAI.

Tres agentes:
  1. Arquitecto            -> diseña la estructura del programa
  2. Programador algoritmos -> escribe BFS y DFS (algoritmos.py)
  3. Programador interfaz   -> escribe la ventana PyQt (interfaz.py)

Los archivos generados se guardan en la carpeta ./salida
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from crewai import Agent, Crew, LLM, Process, Task

load_dotenv()

MODELO_LOCAL = os.getenv("MODELO_LOCAL", "ollama/qwen2.5-coder:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODELO_GEMINI = os.getenv("MODELO_GEMINI", "gemini/gemini-2.0-flash")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()

llm_local = LLM(model=MODELO_LOCAL, base_url=OLLAMA_URL, temperature=0.2)

if GEMINI_KEY:
    llm_nube = LLM(model=MODELO_GEMINI, api_key=GEMINI_KEY, temperature=0.2)
    print(f"[info] Usando Gemini ({MODELO_GEMINI}) para el agente de interfaz.")
else:
    llm_nube = llm_local
    print("[aviso] No hay GEMINI_API_KEY en .env: todos los agentes usarán el modelo local.")


arquitecto = Agent(
    role="Arquitecto de software en Python",
    goal="Diseñar de forma clara y simple la estructura de un programa PyQt que visualiza BFS y DFS",
    backstory=(
        "Eres un ingeniero de software que explica diseños sencillos a estudiantes. "
        "Prefieres pocas clases y nombres claros en español."
    ),
    llm=llm_local,
    allow_delegation=False,
    verbose=True,
)

prog_algoritmos = Agent(
    role="Programador de algoritmos de búsqueda en grafos",
    goal="Escribir BFS y DFS correctos sobre una cuadrícula, devolviendo el orden de exploración y el camino",
    backstory=(
        "Eres experto en estructuras de datos. Escribes código Python limpio, comentado en español, "
        "sin dependencias externas."
    ),
    llm=llm_local,
    allow_delegation=False,
    verbose=True,
)

prog_interfaz = Agent(
    role="Programador de interfaces gráficas con PyQt5",
    goal="Escribir una ventana PyQt5 con cuadrícula, arrastrar y soltar, selector de algoritmo y animación",
    backstory=(
        "Eres especialista en PyQt5. Conoces QGridLayout, QPushButton, QTimer, eventos de arrastrar "
        "y soltar (mousePressEvent, mouseMoveEvent, QDrag, QMimeData, dragEnterEvent, dropEvent) "
        "y escribes código que funciona al primer intento."
    ),
    llm=llm_nube,
    allow_delegation=False,
    verbose=True,
)

REQUISITOS = """
Programa en Python con PyQt5 que visualiza algoritmos de búsqueda en grafos:
- Una cuadrícula (por ejemplo 10x10) donde cada casilla es una celda.
- Hay una casilla de INICIO con una HORMIGA, una META con ALIMENTO y varios OBSTÁCULOS.
- La hormiga, el alimento y los obstáculos se pueden ARRASTRAR Y SOLTAR a otras casillas.
- Un selector (QComboBox) para elegir BÚSQUEDA POR ANCHURA (BFS) o POR PROFUNDIDAD (DFS).
- Un botón "Iniciar" que anima casilla por casilla la exploración (con QTimer) y al final
  marca el camino encontrado. Un botón "Reiniciar" limpia la animación.
- Si no hay camino, mostrar un mensaje.
"""

t_arquitectura = Task(
    description=(
        f"Requisitos del programa:\n{REQUISITOS}\n"
        "Diseña la estructura: lista de archivos (solo algoritmos.py e interfaz.py), "
        "las funciones públicas de algoritmos.py con sus parámetros y lo que devuelven, "
        "y las clases principales de interfaz.py con sus responsabilidades. "
        "Máximo 40 líneas, sin escribir código completo."
    ),
    expected_output="Un documento corto en español con el diseño de archivos, funciones y clases.",
    agent=arquitecto,
)

t_algoritmos = Task(
    description=(
        "Siguiendo el diseño del arquitecto, escribe el archivo algoritmos.py completo.\n"
        "Debe incluir las funciones bfs(filas, columnas, inicio, meta, obstaculos) y "
        "dfs(filas, columnas, inicio, meta, obstaculos). Cada una devuelve una tupla "
        "(orden_visitados, camino) donde orden_visitados es la lista de (fila, col) en el orden "
        "en que se exploraron y camino es la lista de (fila, col) de inicio a meta, o [] si no hay camino. "
        "Movimientos permitidos: arriba, abajo, izquierda, derecha. 'obstaculos' es un set de (fila, col). "
        "Usa collections.deque para BFS y una pila para DFS. Comenta el código en español."
    ),
    expected_output="Solo el código Python completo de algoritmos.py, sin explicaciones fuera del código.",
    agent=prog_algoritmos,
    context=[t_arquitectura],
)

t_interfaz = Task(
    description=(
        "Siguiendo el diseño del arquitecto, escribe el archivo interfaz.py completo con PyQt5.\n"
        f"Requisitos:\n{REQUISITOS}\n"
        "Importa las funciones con: from algoritmos import bfs, dfs  (el módulo ya existe y devuelve "
        "(orden_visitados, camino)). Incluye al final: if __name__ == '__main__': que abra la ventana. "
        "Usa colores distintos: visitadas (azul claro), camino (amarillo), obstáculo (gris oscuro), "
        "inicio/hormiga (rojo con texto 'H'), meta/alimento (verde con texto 'A'). "
        "El arrastrar y soltar debe funcionar para hormiga, alimento y obstáculos, y se bloquea mientras "
        "corre la animación."
    ),
    expected_output="Solo el código Python completo de interfaz.py, sin explicaciones fuera del código.",
    agent=prog_interfaz,
    context=[t_arquitectura, t_algoritmos],
)

equipo = Crew(
    agents=[arquitecto, prog_algoritmos, prog_interfaz],
    tasks=[t_arquitectura, t_algoritmos, t_interfaz],
    process=Process.sequential,
    verbose=True,
)


def limpiar_codigo(texto: str) -> str:
    """Quita los bloques ```python ... ``` si el modelo los puso."""
    bloques = re.findall(r"```(?:python)?\s*\n(.*?)```", texto, flags=re.DOTALL)
    return (max(bloques, key=len) if bloques else texto).strip() + "\n"


def guardar(nombre: str, contenido: str):
    carpeta = Path("salida")
    carpeta.mkdir(exist_ok=True)
    (carpeta / nombre).write_text(contenido, encoding="utf-8")
    print(f"[ok] Guardado salida/{nombre}")


if __name__ == "__main__":
    equipo.kickoff()
    guardar("arquitectura.md", t_arquitectura.output.raw)
    guardar("algoritmos.py", limpiar_codigo(t_algoritmos.output.raw))
    guardar("interfaz.py", limpiar_codigo(t_interfaz.output.raw))
    print("\nListo. Ejecuta el juego con:  cd salida && python interfaz.py")
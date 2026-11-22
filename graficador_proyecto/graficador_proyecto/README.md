# Graficador de expresiones

Intérprete de ecuaciones en Python: construye el **árbol de expresión** y grafica la
función **punto por punto**, con manejo de raíces negativas, divisiones entre cero y
asíntotas.

## Instalación y uso

```
pip install matplotlib          # numpy y pillow vienen con matplotlib
python main.py                  # abre la interfaz (equivale a: python -m graficador)
```

La interfaz usa `tkinter`, que viene con Python en Windows y macOS. En Debian/Ubuntu:
`sudo apt install python3-tk`.

En la ventana escribes la ecuación (`y = ...`), el intervalo `x mín` / `x máx`
(aceptan expresiones: `-2*pi`, `sqrt(2)`), los puntos y la velocidad, y pulsas
**Graficar** o Enter. A la izquierda aparece el árbol; a la derecha la curva se traza
punto por punto, con un punto rojo que marca el avance. Botones: Pausar/Reanudar,
Completar (salta al final), Limpiar y Guardar imágenes.

Modo consola (no necesita ventana):

```
python -m graficador cli "sqrt(2*(x^2)+5*x-3)" --png salida.png
python -m graficador cli "1/x" --xmin=-5 --xmax=5 --gif animacion.gif
python -m graficador cli "sin(x)/x" --xmin=-4*pi --xmax=4*pi
```

## Sintaxis

- Operadores `+ - * / ^` (también `**`), paréntesis y signo unario: `-x^2`, `2^-x`.
- `2^3^2` se lee como `2^(3^2)`; `-x^2` como `-(x^2)`.
- Multiplicación implícita: `2x`, `3(x+1)`, `(x+1)(x-1)`, `2sin(x)`.
- Funciones: `sqrt cbrt abs exp ln log log2 sin cos tan asin acos atan sinh cosh tanh`.
- Constantes: `pi`, `e`. Una sola variable con cualquier nombre (`x`, `t`...).

## Casos especiales

| Caso | Qué hace |
|---|---|
| `sqrt(negativo)`, `ln(x<=0)`, `asin(2)` | No grafica esos puntos, sombrea el intervalo y explica el motivo. |
| Frontera del dominio | La busca por bisección: en `sqrt(2x²+5x-3)` la curva llega exactamente a `x=-3` y `x=0.5`. |
| `1/x`, `tan(x)` | Corta la línea en la asíntota y dibuja una línea roja discontinua. Un cruce por cero empinado no se confunde con una asíntota. |
| `sin(x)/x` en `x=0` | La curva sigue conectada y se avisa de la discontinuidad evitable. |
| `(-8)^(1/3)` | `-2` (raíz real si el exponente es p/q con q impar). `(-4)^0.5` no es real. |
| `0^(-1)`, `exp(1000)`, `10^400` | División entre cero / desbordamiento, controlados. |
| Errores de sintaxis | Mensaje con la posición; la gráfica anterior se conserva. |

## Estructura (cada módulo se puede reutilizar por separado)

| Módulo | Responsabilidad | Dependencias |
|---|---|---|
| `errors.py` | Jerarquía de excepciones | — |
| `funciones.py` | Funciones y constantes con validación de dominio | — |
| `lexer.py` | Texto → tokens (incluye multiplicación implícita) | — |
| `parser.py`, `nodes.py` | Tokens → árbol de expresión | — |
| `evaluador.py` | Evalúa el árbol en reales, sin NaN ni complejos | — |
| `sampling.py` | Muestreo, dominio, asíntotas, límites verticales | — |
| `funcion.py` | Clase `Funcion` (API de alto nivel) | — |
| `tree_text.py` | Árbol en ASCII y forma parentizada | — |
| `tree_draw.py` | Dibuja el árbol en un `Axes` | un `Axes` |
| `plotting.py` | `GraficaPorPuntos`: animación sobre un `Axes` | matplotlib |
| `sesion.py` | Validación de campos y flujo de la animación | matplotlib |
| `gui.py` | Ventana (solo widgets) | tkinter |
| `cli.py` | Consola, PNG y GIF | matplotlib, pillow |

Uso del núcleo como librería (sin dependencias):

```python
from graficador import Funcion, DominioError

f = Funcion("sqrt(2*(x^2)+5*x-3)")
f(1)                          # 2.0
try:
    f(0)
except DominioError as e:
    print(e)                  # raíz cuadrada de un número negativo: argumento = -3
print(f.arbol_ascii())
m = f.muestrear(-10, 10, 800) # m.xs, m.ys (NaN = corte), m.indefinidos, m.asintotas
print(m.resumen())
```

Para agregar una función nueva (por ejemplo `sec`), defínela en `funciones.py` y
regístrala en `FUNCIONES`: el lexer, el parser y el evaluador la reconocen solos.

## Pruebas

```
python -m unittest discover -s tests -v
```

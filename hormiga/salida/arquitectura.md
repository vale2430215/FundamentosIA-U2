### Diseño del Programa

#### Archivo: algoritmos.py

**Funciones Públicas:**

1. **`bfs(grafica, inicio, meta)`**
   - **Parámetros:** `grafica` (dict), `inicio` (tuple), `meta` (tuple)
   - **Devuelve:** `ruta` (list) o `None` si no hay camino

2. **`dfs(grafica, inicio, meta)`**
   - **Parámetros:** `grafica` (dict), `inicio` (tuple), `meta` (tuple)
   - **Devuelve:** `ruta` (list) o `None` si no hay camino

#### Archivo: interfaz.py

**Clases Principales:**

1. **`VentanaPrincipal(QMainWindow)`**
   - **Responsabilidades:**
     - Diseña la interfaz gráfica.
     - Maneja eventos de arrastrar y soltar.
     - Actualiza la interfaz con el estado del algoritmo.

2. **`Grafica(QGraphicsScene)`**
   - **Responsabilidades:**
     - Representa la cuadrícula del juego.
     - Maneja la creación y movimiento de elementos (hormiga, alimento, obstáculos).

3. **`Controlador(QThread)`**
   - **Responsabilidades:**
     - Ejecuta el algoritmo seleccionado (BFS o DFS) en un hilo separado.
     - Actualiza la interfaz con el progreso del algoritmo.

### Diagrama de Clases

```
VentanaPrincipal
  ├── Grafica
  └── Controlador
```

### Explicación

- **`algoritmos.py`**: Contiene las implementaciones de los algoritmos BFS y DFS. Estas funciones toman una representación del grafo y los nodos inicio y meta, y devuelven la ruta encontrada o `None` si no hay camino.

- **`interfaz.py`**: Contiene la interfaz gráfica principal (`VentanaPrincipal`). Esta clase maneja la creación de la interfaz, el manejo de eventos de arrastrar y soltar, y la actualización de la interfaz según el estado del algoritmo.

- **`Grafica`**: Es una clase que hereda de `QGraphicsScene`. Se encarga de representar la cuadrícula y manejar la interacción con los elementos gráficos (hormiga, alimento, obstáculos).

- **`Controlador`**: Es una clase que hereda de `QThread`. Se encarga de ejecutar el algoritmo en un hilo separado, lo que permite mantener la interfaz gráfica responsive mientras se ejecuta el algoritmo.

Este diseño permite una separación clara de responsabilidades y facilita la implementación y pruebas de cada componente del programa.
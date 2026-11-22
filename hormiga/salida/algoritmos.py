from collections import deque

def bfs(filas, columnas, inicio, meta, obstaculos):
    """
    Realiza una búsqueda en amplitud (BFS) en una cuadrícula.

    :param filas: Número de filas de la cuadrícula
    :param columnas: Número de columnas de la cuadrícula
    :param inicio: Tupla (fila, columna) del nodo de inicio
    :param meta: Tupla (fila, columna) del nodo meta
    :param obstaculos: Conjunto de tuplas (fila, columna) que representan los obstáculos
    :return: Tupla (orden_visitados, camino) o (None, None) si no hay camino
    """
    # Direcciones posibles de movimiento: arriba, abajo, izquierda, derecha
    direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Inicializar la cola y el conjunto de visitados
    cola = deque([inicio])
    visitados = set([inicio])
    padre = {inicio: None}
    
    while cola:
        actual = cola.popleft()
        
        # Si se llega al nodo meta, reconstruir el camino
        if actual == meta:
            camino = []
            while actual:
                camino.append(actual)
                actual = padre[actual]
            camino.reverse()
            return (list(visitados), camino)
        
        # Explorar los vecinos
        for df, dc in direcciones:
            vecino = (actual[0] + df, actual[1] + dc)
            if 0 <= vecino[0] < filas and 0 <= vecino[1] < columnas and vecino not in visitados and vecino not in obstaculos:
                cola.append(vecino)
                visitados.add(vecino)
                padre[vecino] = actual
    
    # Si no se encuentra un camino
    return (None, None)

def dfs(filas, columnas, inicio, meta, obstaculos):
    """
    Realiza una búsqueda en profundidad (DFS) en una cuadrícula.

    :param filas: Número de filas de la cuadrícula
    :param columnas: Número de columnas de la cuadrícula
    :param inicio: Tupla (fila, columna) del nodo de inicio
    :param meta: Tupla (fila, columna) del nodo meta
    :param obstaculos: Conjunto de tuplas (fila, columna) que representan los obstáculos
    :return: Tupla (orden_visitados, camino) o (None, None) si no hay camino
    """
    # Direcciones posibles de movimiento: arriba, abajo, izquierda, derecha
    direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Inicializar la pila y el conjunto de visitados
    pila = [inicio]
    visitados = set([inicio])
    padre = {inicio: None}
    
    while pila:
        actual = pila.pop()
        
        # Si se llega al nodo meta, reconstruir el camino
        if actual == meta:
            camino = []
            while actual:
                camino.append(actual)
                actual = padre[actual]
            camino.reverse()
            return (list(visitados), camino)
        
        # Explorar los vecinos en orden inverso para DFS
        for df, dc in reversed(direcciones):
            vecino = (actual[0] + df, actual[1] + dc)
            if 0 <= vecino[0] < filas and 0 <= vecino[1] < columnas and vecino not in visitados and vecino not in obstaculos:
                pila.append(vecino)
                visitados.add(vecino)
                padre[vecino] = actual
    
    # Si no se encuentra un camino
    return (None, None)

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QComboBox, QPushButton,
                             QVBoxLayout, QWidget, QLabel, QGraphicsScene,
                             QGraphicsView, QGraphicsRectItem, QGraphicsSimpleTextItem)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPen, QBrush, QFont

from algoritmos import bfs, dfs

FILAS = 10
COLUMNAS = 10
TAM = 50  

COLOR_LIBRE = QColor(255, 255, 255)
COLOR_HORMIGA = QColor(220, 40, 40)
COLOR_ALIMENTO = QColor(40, 170, 70)
COLOR_META = QColor(40, 90, 200)
COLOR_OBSTACULO = QColor(70, 70, 70)
COLOR_VISITADA = QColor(173, 216, 230)  
COLOR_CAMINO = QColor(255, 220, 0)       
COLOR_VISITADA2 = QColor(221, 200, 240)  
COLOR_CAMINO2 = QColor(255, 150, 60)


class Grafica(QGraphicsScene):
    """Cuadrícula. Guarda dónde están la hormiga, el alimento, la meta y los
    obstáculos, y permite arrastrarlos con el ratón."""

    def __init__(self, filas, columnas, parent=None):
        super().__init__(parent)
        self.filas = filas
        self.columnas = columnas
        self.setSceneRect(0, 0, columnas * TAM, filas * TAM)

        self.casillas = {}   
        self.textos = {}     
        self.hormiga = (0, 0)
        self.alimento = (0, columnas - 1)
        self.meta = (filas - 1, columnas - 1)
        self.obstaculos = {(5, 5), (5, 6), (6, 5), (6, 6)}

        self.visitadas = set()
        self.camino = set()
        self.visitadas2 = set()
        self.camino2 = set()

        self.bloqueado = False      
        self.arrastrando = None
        self.celda_actual = None
        self.se_movio = False

        self._crear_casillas()
        self.refrescar()

    def _crear_casillas(self):
        fuente = QFont("Arial", 18, QFont.Bold)
        for f in range(self.filas):
            for c in range(self.columnas):
                rect = QGraphicsRectItem(c * TAM, f * TAM, TAM, TAM)
                rect.setPen(QPen(Qt.black))
                self.addItem(rect)
                self.casillas[(f, c)] = rect

                texto = QGraphicsSimpleTextItem("")
                texto.setFont(fuente)
                texto.setBrush(QBrush(Qt.white))
                texto.setAcceptedMouseButtons(Qt.NoButton)
                self.addItem(texto)
                self.textos[(f, c)] = texto

    def refrescar(self):
        """Pinta cada casilla según lo que contiene."""
        for celda, rect in self.casillas.items():
            letra = ""
            if celda == self.hormiga:
                color, letra = COLOR_HORMIGA, "H"
            elif celda == self.alimento:
                color, letra = COLOR_ALIMENTO, "A"
            elif celda == self.meta:
                color, letra = COLOR_META, "M"
            elif celda in self.obstaculos:
                color = COLOR_OBSTACULO
            elif celda in self.camino2:
                color = COLOR_CAMINO2
            elif celda in self.camino:
                color = COLOR_CAMINO
            elif celda in self.visitadas2:
                color = COLOR_VISITADA2
            elif celda in self.visitadas:
                color = COLOR_VISITADA
            else:
                color = COLOR_LIBRE
            rect.setBrush(QBrush(color))

            texto = self.textos[celda]
            texto.setText(letra)
            caja = texto.boundingRect()
            texto.setPos(celda[1] * TAM + (TAM - caja.width()) / 2,
                         celda[0] * TAM + (TAM - caja.height()) / 2)

    def limpiar_animacion(self):
        self.visitadas.clear()
        self.camino.clear()
        self.visitadas2.clear()
        self.camino2.clear()
        self.refrescar()

    def _celda_en(self, pos):
        fila, columna = int(pos.y() // TAM), int(pos.x() // TAM)
        if 0 <= fila < self.filas and 0 <= columna < self.columnas:
            return (fila, columna)
        return None

    def _tipo_en(self, celda):
        if celda == self.hormiga:
            return 'hormiga'
        if celda == self.alimento:
            return 'alimento'
        if celda == self.meta:
            return 'meta'
        if celda in self.obstaculos:
            return 'obstaculo'
        return None

    def _mover(self, tipo, origen, destino):
        if tipo == 'hormiga':
            self.hormiga = destino
        elif tipo == 'alimento':
            self.alimento = destino
        elif tipo == 'meta':
            self.meta = destino
        else:
            self.obstaculos.discard(origen)
            self.obstaculos.add(destino)

    def mousePressEvent(self, event):
        if self.bloqueado or event.button() != Qt.LeftButton:
            return
        celda = self._celda_en(event.scenePos())
        if celda is None:
            return
        tipo = self._tipo_en(celda)
        if tipo is None:
            self.obstaculos.add(celda)
            tipo = 'obstaculo'
            self.se_movio = True   
            self.refrescar()
        else:
            self.se_movio = False
        self.arrastrando = tipo
        self.celda_actual = celda

    def mouseMoveEvent(self, event):
        if self.arrastrando is None:
            return
        celda = self._celda_en(event.scenePos())
        if celda is None or celda == self.celda_actual:
            return
        if self._tipo_en(celda) is not None:
            return  
        self._mover(self.arrastrando, self.celda_actual, celda)
        self.celda_actual = celda
        self.se_movio = True
        self.refrescar()

    def mouseReleaseEvent(self, event):
        if self.arrastrando == 'obstaculo' and not self.se_movio:
            self.obstaculos.discard(self.celda_actual)
            self.refrescar()
        self.arrastrando = None
        self.celda_actual = None


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hormiga buscadora: BFS vs DFS")

        self.grafica = Grafica(FILAS, COLUMNAS)
        self.vista = QGraphicsView(self.grafica) 
        borde = self.vista.frameWidth() * 2
        self.vista.setFixedSize(COLUMNAS * TAM + borde, FILAS * TAM + borde)
        self.vista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.vista.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.selector = QComboBox()
        self.selector.addItem("Búsqueda por anchura (BFS)", "bfs")
        self.selector.addItem("Búsqueda por profundidad (DFS)", "dfs")

        self.boton_iniciar = QPushButton("Iniciar")
        self.boton_iniciar.clicked.connect(self.iniciar)
        self.boton_reiniciar = QPushButton("Reiniciar")
        self.boton_reiniciar.clicked.connect(self.reiniciar)

        self.etiqueta = QLabel(self.TEXTO_AYUDA)
        self.etiqueta.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.vista)
        layout.addWidget(self.selector)
        layout.addWidget(self.boton_iniciar)
        layout.addWidget(self.boton_reiniciar)
        layout.addWidget(self.etiqueta)
        contenedor = QWidget()
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

        # animación
        self.timer = QTimer()
        self.timer.timeout.connect(self.avanzar)
        self.pasos = []         
        self.resumen = ""

    TEXTO_AYUDA = ("H = hormiga, A = alimento, M = meta (salida). La hormiga busca primero "
                   "el alimento y después la meta. Arrastra las piezas; clic en una casilla "
                   "vacía crea un obstáculo y clic en un obstáculo lo quita.")

    def iniciar(self):
        if self.timer.isActive():
            return
        g = self.grafica
        g.limpiar_animacion()
        algoritmo = bfs if self.selector.currentData() == "bfs" else dfs
        obstaculos = set(g.obstaculos)

        orden1, camino1 = algoritmo(FILAS, COLUMNAS, g.hormiga, g.alimento, obstaculos)
        self.pasos = [(list(orden1), g.visitadas), (list(camino1), g.camino)]

        if not camino1:
            self.resumen = (f"No hay camino hacia el alimento. "
                            f"Casillas exploradas: {len(orden1)}.")
        else:
            orden2, camino2 = algoritmo(FILAS, COLUMNAS, g.alimento, g.meta, obstaculos)
            self.pasos += [(list(orden2), g.visitadas2), (list(camino2), g.camino2)]
            parte1 = (f"Alimento: {len(camino1) - 1} pasos "
                      f"({len(orden1)} casillas exploradas).")
            if camino2:
                self.resumen = (f"{parte1} Meta: {len(camino2) - 1} pasos "
                                f"({len(orden2)} exploradas). "
                                f"Total: {len(camino1) + len(camino2) - 2} pasos.")
            else:
                self.resumen = (f"{parte1} Pero no hay camino desde el alimento hacia la meta "
                                f"({len(orden2)} exploradas).")

        g.bloqueado = True
        self.boton_iniciar.setEnabled(False)
        self.selector.setEnabled(False)
        self.etiqueta.setText("Buscando el alimento...")
        self.timer.start(100)

    def avanzar(self):
        while self.pasos and not self.pasos[0][0]:
            self.pasos.pop(0)
            if len(self.pasos) == 2:
                self.etiqueta.setText("Alimento encontrado. Buscando la meta...")
        if not self.pasos:
            self.terminar()
            return
        pendientes, destino = self.pasos[0]
        destino.add(pendientes.pop(0))
        self.grafica.refrescar()

    def terminar(self):
        self.timer.stop()
        self.grafica.bloqueado = False
        self.boton_iniciar.setEnabled(True)
        self.selector.setEnabled(True)
        self.etiqueta.setText(self.resumen)

    def reiniciar(self):
        self.timer.stop()
        self.pasos = []
        self.grafica.bloqueado = False
        self.grafica.limpiar_animacion()
        self.boton_iniciar.setEnabled(True)
        self.selector.setEnabled(True)
        self.etiqueta.setText(self.TEXTO_AYUDA)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec_())
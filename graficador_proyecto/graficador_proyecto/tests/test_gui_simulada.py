"""Prueba de humo de gui.py con tkinter SIMULADO (sirve donde no hay entorno gráfico).

No comprueba el aspecto de la ventana; comprueba que el flujo de la interfaz
(graficar, animar, pausar, completar, limpiar, errores) ejecuta sin fallos y
conecta bien con Sesion.
"""

import sys
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class _Var:
    def __init__(self, value=None, **_):
        self._v = value

    def get(self):
        return self._v

    def set(self, v):
        self._v = v


class _Widget:
    """Widget falso: acepta cualquier configuración y cualquier método."""

    def __init__(self, *a, **k):
        pass

    def winfo_children(self):
        return []

    def __getattr__(self, nombre):
        return lambda *a, **k: None


class _Texto(_Widget):
    def __init__(self, *a, **k):
        self.contenido = []

    def delete(self, *a):
        self.contenido.clear()

    def insert(self, _pos, linea, etiqueta=()):
        self.contenido.append((linea.strip(), etiqueta))


class _Raiz:
    def __init__(self):
        self.cola = {}
        self.n = 0
        self.destruida = False

    def after(self, _ms, fn=None):
        self.n += 1
        self.cola[self.n] = fn
        return self.n

    def after_cancel(self, ident):
        self.cola.pop(ident, None)

    def __getattr__(self, nombre):      # title, geometry, columnconfigure, protocol...
        return lambda *a, **k: None

    def destroy(self):
        self.destruida = True

    def correr(self, max_pasos=5000):
        """Ejecuta los temporizadores pendientes, de uno en uno, como haría Tk."""
        pasos = 0
        while self.cola and pasos < max_pasos:
            ident = min(self.cola)
            self.cola.pop(ident)()
            pasos += 1
        return pasos


class _Canvas:
    def __init__(self, fig, master=None):
        self.fig = fig
        self.dibujos = 0

    def draw_idle(self):
        self.dibujos += 1

    def get_tk_widget(self):
        return mock.MagicMock()


def _instalar_tk_falso():
    tk = types.ModuleType("tkinter")
    tk.Tk = _Raiz
    tk.StringVar = _Var
    tk.DoubleVar = _Var
    tk.Text = _Texto
    ttk = types.ModuleType("tkinter.ttk")
    for nombre in ("Frame", "Label", "Entry", "Button", "Spinbox", "Scale", "PanedWindow"):
        setattr(ttk, nombre, _Widget)
    filedialog = types.ModuleType("tkinter.filedialog")
    filedialog.asksaveasfilename = lambda **k: ""
    tk.ttk, tk.filedialog = ttk, filedialog
    back = types.ModuleType("matplotlib.backends.backend_tkagg")
    back.FigureCanvasTkAgg = _Canvas
    back.NavigationToolbar2Tk = _Widget
    return {"tkinter": tk, "tkinter.ttk": ttk, "tkinter.filedialog": filedialog,
            "matplotlib.backends.backend_tkagg": back}


class TestGuiSimulada(unittest.TestCase):
    def setUp(self):
        self.parche = mock.patch.dict(sys.modules, _instalar_tk_falso())
        self.parche.start()
        sys.modules.pop("graficador.gui", None)
        import graficador.gui as gui
        self.gui = gui
        self.raiz = _Raiz()
        self.app = gui.Aplicacion(self.raiz)

    def tearDown(self):
        sys.modules.pop("graficador.gui", None)
        self.parche.stop()

    def texto_estado(self):
        return [t for t, _ in self.app.txt_estado.contenido]

    def test_ejemplo_inicial_se_anima_hasta_el_final(self):
        pasos = self.raiz.correr()           # dispara graficar() y luego los _tic
        self.assertGreater(pasos, 10)
        self.assertTrue(self.app.sesion.animacion.terminada)
        self.assertGreater(self.app.canvas_graf.dibujos, 10)
        self.assertTrue(any("Interpretada como" in t for t in self.texto_estado()))
        self.assertTrue(any("Sin valores reales" in t for t in self.texto_estado()))

    def test_error_de_sintaxis_se_muestra_y_no_rompe(self):
        self.raiz.correr()
        previa = self.app.sesion.animacion
        self.app.var_expr.set("2*(x+")
        self.app.graficar()
        self.assertTrue(any("Error en la ecuación" in t for t in self.texto_estado()))
        self.assertIn("error", [e for _, e in self.app.txt_estado.contenido][0])
        self.assertIs(self.app.sesion.animacion, previa)

    def test_intervalo_invalido(self):
        self.app.var_xmin.set("5")
        self.app.var_xmax.set("1")
        self.app.graficar()
        self.assertTrue(any("menor" in t for t in self.texto_estado()))

    def test_pausar_reanudar_completar(self):
        self.app.var_expr.set("sin(x)")
        self.app.var_xmin.set("-2*pi")
        self.app.var_xmax.set("2*pi")
        self.app.graficar()
        # avanzar unos pocos cuadros y pausar
        for _ in range(3):
            self.raiz.cola.pop(min(self.raiz.cola))()
        k = self.app.sesion.animacion._k
        self.app.pausar()
        self.assertTrue(self.app._pausado)
        self.assertEqual(self.raiz.cola, {})          # sin temporizadores pendientes
        self.assertEqual(self.app.sesion.animacion._k, k)
        self.app.pausar()                             # reanudar
        self.assertFalse(self.app._pausado)
        self.assertTrue(self.raiz.cola)
        self.app.completar()
        self.assertTrue(self.app.sesion.animacion.terminada)

    def test_limpiar(self):
        self.raiz.correr()
        self.app.limpiar()
        self.assertFalse(self.app.sesion.activa)

    def test_cerrar_cancela_temporizador(self):
        self.app.graficar()
        self.app._cerrar()
        self.assertTrue(self.raiz.destruida)
        self.assertIsNone(self.app._after_id)


if __name__ == "__main__":
    unittest.main()

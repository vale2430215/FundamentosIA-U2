"""Pruebas del núcleo: parser, evaluador, dominio, asíntotas, animación y sesión.

Ejecutar desde la carpeta del proyecto:   python -m unittest discover -s tests -v
"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graficador import (DivisionCeroError, DominioError, ExpresionError, Funcion,  # noqa: E402
                        SintaxisError, VariableError, a_texto, construir_arbol,
                        evaluar_constante)


def txt(s: str) -> str:
    return a_texto(construir_arbol(s))


class TestParser(unittest.TestCase):
    def test_precedencia(self):
        self.assertEqual(txt("1+2*3"), "(1 + (2 * 3))")
        self.assertEqual(txt("(1+2)*3"), "((1 + 2) * 3)")

    def test_asociatividad(self):
        self.assertEqual(txt("10-3-2"), "((10 - 3) - 2)")
        self.assertEqual(txt("2^3^2"), "(2 ^ (3 ^ 2))")
        self.assertEqual(txt("8/4/2"), "((8 / 4) / 2)")

    def test_unario(self):
        self.assertEqual(txt("-x^2"), "(-(x ^ 2))")
        self.assertEqual(txt("2^-x"), "(2 ^ (-x))")
        self.assertEqual(txt("--x"), "(-(-x))")

    def test_multiplicacion_implicita(self):
        self.assertEqual(txt("2x"), "(2 * x)")
        self.assertEqual(txt("3(x+1)"), "(3 * (x + 1))")
        self.assertEqual(txt("(x+1)(x-1)"), "((x + 1) * (x - 1))")
        self.assertEqual(txt("2sin(x)"), "(2 * sin(x))")

    def test_notaciones_alternativas(self):
        self.assertEqual(txt("x**2"), "(x ^ 2)")
        self.assertEqual(txt("x²"), "(x ^ 2)")

    def test_ejemplo_del_enunciado(self):
        self.assertEqual(txt("sqrt(2*(x^2)+5*x-3)"), "sqrt((((2 * (x ^ 2)) + (5 * x)) - 3))")

    def test_errores_de_sintaxis(self):
        for malo in ["", "   ", "2*(x+", "(x+1))", "sqrt x", "2 $ 3", "()", "2+", "*3", "1e999"]:
            with self.subTest(malo=malo):
                with self.assertRaises(SintaxisError):
                    construir_arbol(malo)

    def test_posicion_del_error(self):
        with self.assertRaises(SintaxisError) as cm:
            construir_arbol("2 + $")
        self.assertEqual(cm.exception.posicion, 4)


class TestEvaluacion(unittest.TestCase):
    def test_valores(self):
        f = Funcion("sqrt(2*(x^2)+5*x-3)")
        self.assertAlmostEqual(f(1), 2.0)
        self.assertAlmostEqual(f(-3), 0.0)
        self.assertAlmostEqual(f(0.5), 0.0)
        self.assertAlmostEqual(Funcion("1e3*x")(2), 2000.0)
        self.assertAlmostEqual(Funcion("x^2")(-3), 9.0)

    def test_raiz_de_negativo(self):
        with self.assertRaises(DominioError):
            Funcion("sqrt(2*(x^2)+5*x-3)")(0)
        with self.assertRaises(DominioError):
            Funcion("sqrt(x)")(-1)

    def test_division_entre_cero(self):
        with self.assertRaises(DivisionCeroError):
            Funcion("1/x")(0)
        with self.assertRaises(DivisionCeroError):
            Funcion("1/(x-2)")(2)
        with self.assertRaises(DivisionCeroError):
            Funcion("0/x")(0)

    def test_potencias(self):
        self.assertAlmostEqual(evaluar_constante("(-8)^(1/3)"), -2.0)
        self.assertAlmostEqual(evaluar_constante("(-8)^(2/3)"), 4.0)
        self.assertAlmostEqual(evaluar_constante("(-2)^3"), -8.0)
        self.assertEqual(evaluar_constante("0^0"), 1.0)
        with self.assertRaises(DominioError):
            evaluar_constante("(-4)^0.5")
        with self.assertRaises(DominioError):
            evaluar_constante("(-2)^pi")
        with self.assertRaises(DivisionCeroError):
            evaluar_constante("0^(-1)")

    def test_dominios_de_funciones(self):
        for malo in ["ln(0)", "ln(-1)", "log(-5)", "asin(2)", "acos(-2)", "exp(1000)",
                     "10^400", "sqrt(-1)"]:
            with self.subTest(malo=malo):
                with self.assertRaises(DominioError):
                    evaluar_constante(malo)
        self.assertAlmostEqual(evaluar_constante("cbrt(-27)"), -3.0)

    def test_variables(self):
        with self.assertRaises(VariableError):
            Funcion("x+y")
        with self.assertRaises(VariableError):
            evaluar_constante("x+1")
        self.assertAlmostEqual(evaluar_constante("-2*pi"), -2 * math.pi)
        self.assertEqual(Funcion("t^2").variable, "t")
        self.assertAlmostEqual(Funcion("t^2")(3), 9.0)

    def test_errores_comparten_base(self):
        with self.assertRaises(ExpresionError):
            Funcion("sqrt(x)")(-1)


class TestMuestreo(unittest.TestCase):
    def test_raiz_con_dominio_partido(self):
        m = Funcion("sqrt(2*(x^2)+5*x-3)").muestrear(-10, 10, 801)
        self.assertEqual(len(m.indefinidos), 1)
        iv = m.indefinidos[0]
        self.assertAlmostEqual(iv.inicio, -3.0, places=9)
        self.assertAlmostEqual(iv.fin, 0.5, places=9)
        self.assertTrue(iv.abierto_izq and iv.abierto_der)
        self.assertEqual(m.asintotas, [])
        # la curva llega hasta la frontera: hay puntos con y ~ 0 en x ~ -3 y x ~ 0.5
        cerca = [(x, y) for x, y in zip(m.xs, m.ys) if not math.isnan(y) and y < 1e-3]
        self.assertTrue(any(abs(x + 3) < 1e-6 for x, _ in cerca))
        self.assertTrue(any(abs(x - 0.5) < 1e-6 for x, _ in cerca))
        self.assertGreaterEqual(min(y for y in m.ys if not math.isnan(y)), 0.0)

    def test_sin_valores_reales(self):
        m = Funcion("sqrt(-1)").muestrear(-5, 5, 100)
        self.assertEqual(m.n_validos, 0)
        self.assertIn("no toma valores reales", m.resumen()[0])

    def test_logaritmo(self):
        m = Funcion("ln(x)").muestrear(-5, 5, 400)
        iv = m.indefinidos[0]
        self.assertAlmostEqual(iv.fin, 0.0, places=6)
        self.assertEqual(iv.inicio, -5)

    def test_asintota_en_cero_exacto_y_aproximado(self):
        for n in (800, 801):          # 801 incluye x = 0 exacto
            with self.subTest(n=n):
                m = Funcion("1/x").muestrear(-10, 10, n)
                self.assertEqual(len(m.asintotas), 1)
                self.assertLess(abs(m.asintotas[0]), 0.05)
                self.assertTrue(any(math.isnan(y) for y in m.ys))   # línea cortada
                self.assertLess(m.ymax, 20)                          # eje vertical razonable

    def test_tangente(self):
        m = Funcion("tan(x)").muestrear(-5, 5, 1000)
        esperadas = [-3 * math.pi / 2, -math.pi / 2, math.pi / 2, 3 * math.pi / 2]
        self.assertEqual(len(m.asintotas), 4)
        for a, e in zip(m.asintotas, esperadas):
            self.assertLess(abs(a - e), 0.02)

    def test_cruce_empinado_no_es_asintota(self):
        m = Funcion("100*sin(x)*exp(-x^2)").muestrear(-10, 10, 800)
        self.assertEqual(m.asintotas, [])
        self.assertFalse(any(math.isnan(y) for y in m.ys))

    def test_discontinuidad_evitable(self):
        m = Funcion("sin(x)/x").muestrear(-10, 10, 801)
        self.assertEqual(m.asintotas, [])
        self.assertFalse(any(math.isnan(y) for y in m.ys))          # curva conectada
        self.assertTrue(m.indefinidos[0].evitable)
        self.assertIn("evitable", " ".join(m.resumen()))

    def test_division_siempre_cero(self):
        m = Funcion("1/0").muestrear(-1, 1, 50)
        self.assertEqual(m.n_validos, 0)
        self.assertEqual(m.asintotas, [])

    def test_funcion_constante(self):
        m = Funcion("5").muestrear(-3, 3, 50)
        self.assertLess(m.ymin, 5)
        self.assertGreater(m.ymax, 5)

    def test_potencia_con_raiz_real(self):
        m = Funcion("x^(1/3)").muestrear(-8, 8, 321)
        self.assertEqual(m.indefinidos, [])
        self.assertAlmostEqual(min(y for y in m.ys if not math.isnan(y)), -2.0, places=6)

    def test_parametros_invalidos(self):
        f = Funcion("x")
        for args in [(1, 1, 10), (2, 1, 10), (0, 1, 1), (float("nan"), 1, 10), (0, float("inf"), 10)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    f.muestrear(*args)


try:
    from matplotlib.figure import Figure
    HAY_MPL = True
except ImportError:                                           # pragma: no cover
    HAY_MPL = False


@unittest.skipUnless(HAY_MPL, "requiere matplotlib")
class TestAnimacionYSesion(unittest.TestCase):
    def test_animacion_punto_por_punto(self):
        from graficador.plotting import GraficaPorPuntos
        ax = Figure().add_subplot(111)
        m = Funcion("1/x").muestrear(-5, 5, 200)
        anim = GraficaPorPuntos(ax, m, "y = 1/x")
        self.assertEqual(len(anim._linea.get_xdata()), 0)
        self.assertFalse(anim.avanzar(10))
        self.assertEqual(len(anim._linea.get_xdata()), 10)
        self.assertFalse(anim.avanzar(10))
        self.assertEqual(len(anim._linea.get_xdata()), 20)
        self.assertFalse(anim._asintotas[0][1].get_visible())      # aún no llegó a x = 0
        pasos = 0
        while not anim.avanzar(25):
            pasos += 1
            self.assertLess(pasos, 100)
        self.assertEqual(len(anim._linea.get_xdata()), anim.total)
        self.assertTrue(anim._asintotas[0][1].get_visible())
        self.assertEqual(anim.progreso, 1.0)

    def test_sesion_flujo_normal(self):
        from graficador.sesion import Sesion
        fig = Figure()
        s = Sesion(fig.add_subplot(121), fig.add_subplot(122))
        info = s.iniciar("sqrt(2*(x^2)+5*x-3)", "-10", "10", "400")
        self.assertTrue(any("Sin valores reales" in l for l in info))
        self.assertTrue(s.activa)
        n = 0
        while not s.avanzar(20):
            n += 1
        self.assertGreater(n, 5)

    def test_sesion_valida_entradas(self):
        from graficador.sesion import ErrorEntrada, Sesion
        fig = Figure()
        s = Sesion(fig.add_subplot(121), fig.add_subplot(122))
        casos = [
            ("2*(x+", "-1", "1", "100"),     # sintaxis
            ("x+y", "-1", "1", "100"),       # dos variables
            ("x", "abc", "1", "100"),        # límite inferior no válido
            ("x", "-1", "x", "100"),         # límite con variable
            ("x", "1", "1", "100"),          # min == max
            ("x", "2", "1", "100"),          # min > max
            ("x", "-1", "1", "abc"),         # puntos no entero
            ("x", "-1", "1", "1"),           # muy pocos puntos
            ("x", "-1", "1", "99999999"),    # demasiados
            ("x", "1/0", "1", "100"),        # límite con división entre cero
        ]
        for caso in casos:
            with self.subTest(caso=caso):
                with self.assertRaises(ErrorEntrada):
                    s.iniciar(*caso)
        self.assertFalse(s.activa)           # los errores no dejan estado a medias

    def test_error_conserva_grafica_anterior(self):
        from graficador.sesion import ErrorEntrada, Sesion
        fig = Figure()
        s = Sesion(fig.add_subplot(121), fig.add_subplot(122))
        s.iniciar("x^2", "-2", "2", "100")
        anterior = s.animacion
        with self.assertRaises(ErrorEntrada):
            s.iniciar("x+", "-2", "2", "100")
        self.assertIs(s.animacion, anterior)

    def test_limites_con_expresiones(self):
        from graficador.sesion import Sesion
        fig = Figure()
        s = Sesion(fig.add_subplot(121), fig.add_subplot(122))
        s.iniciar("sin(x)", "-2*pi", "2*pi", "300")
        self.assertAlmostEqual(s.animacion.m.xmin, -2 * math.pi)
        self.assertAlmostEqual(s.animacion.m.xmax, 2 * math.pi)


if __name__ == "__main__":
    unittest.main()

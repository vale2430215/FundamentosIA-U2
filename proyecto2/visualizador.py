"""
VISUALIZADOR GENERACION POR GENERACION (sin DEAP)
==================================================
Grafica la funcion y muestra como se mueven los individuos en CADA generacion.

Ventana interactiva:
  - Arriba: la funcion y los individuos de la generacion actual
        * 1 variable  -> la curva f(x) con cada individuo como punto (x, f(x))
        * 2 variables -> curvas de nivel con cada individuo como punto (x1, x2)
        * 3+ variables -> valor de cada variable de cada individuo
  - Abajo: evolucion del mejor y la media, con una linea en la generacion actual
  - Controles: barra deslizante, botones |<  <  Play/Pausa  >  >|
    y teclado (flechas izquierda/derecha, espacio = play/pausa)

Tambien puede guardar la animacion como GIF con --gif.

Ejemplos:
    python visualizador.py max2
    python visualizador.py schwefel --n 2 --num_gen 80
    python visualizador.py rastrigin --n 2 --gif rastrigin.gif
    (en el Proyecto 2 se puede elegir el cruce:  --cruce sbx)
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.widgets import Button, Slider

from funciones import TODAS, obtener_funcion

# Se usa el AG de la carpeta en la que esta este archivo
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ag_binario.py")):
    import ag_binario as ag
    PROYECTO = 1
else:
    import ag_real as ag
    PROYECTO = 2

AZUL, NARANJA, GRIS, AMARILLO = "#2a78d6", "#eb6834", "#8a8984", "#eda100"


def ejecutar_ag(args):
    config = obtener_funcion(args.funcion, args.n)
    comunes = dict(tam_pob=args.tam_pob, num_gen=args.num_gen, prob_cruce=args.prob_cruce,
                   prob_mut=args.prob_mut, elitismo=not args.sin_elitismo, semilla=args.semilla)
    if PROYECTO == 1:
        res = ag.algoritmo_genetico(config, TOL=args.TOL, **comunes)
    else:
        res = ag.algoritmo_genetico(config, tipo_cruce=args.cruce, **comunes)
    return config, res


class Visualizador:
    def __init__(self, config, res, titulo, interactivo=True):
        self.c, self.res = config, res
        self.f = config["f"]
        self.n = config["n"]
        self.pobs = res["poblaciones"]                     # {generacion: matriz tam_pob x n}
        self.num_gen = max(self.pobs)
        # valor de f de cada individuo en cada generacion
        self.fvals = {g: np.array([self.f(np.array(x)) for x in p]) for g, p in self.pobs.items()}
        self.gen = 0
        self.reproduciendo = False

        alto = 8.5 if interactivo else 7.8
        self.fig = plt.figure(figsize=(10, alto))
        # con 1 o 3+ variables la leyenda va a la derecha, fuera de la grafica
        ancho = 0.70 if self.n != 2 else 0.86
        if interactivo:
            self.ax = self.fig.add_axes([0.08, 0.50, ancho, 0.38])
            self.ax_ev = self.fig.add_axes([0.08, 0.17, 0.70, 0.24])
        else:
            self.ax = self.fig.add_axes([0.08, 0.43, ancho, 0.45])
            self.ax_ev = self.fig.add_axes([0.08, 0.07, 0.70, 0.26])
        self.fig.suptitle(titulo, fontsize=12, fontweight="bold")

        self.dibujar_fondo()
        self.dibujar_evolucion()
        if interactivo:
            self.crear_controles()
        self.actualizar(0)

    # ------------------------------------------------------------------ fondo
    def dibujar_fondo(self):
        ax, c = self.ax, self.c
        if self.n == 1:
            xs = np.linspace(c["x_min"][0], c["x_max"][0], 3000)
            ax.plot(xs, [self.f(np.array([x])) for x in xs], color=AZUL, lw=1.2, zorder=1)
            ax.set_xlabel("x")
            ax.set_ylabel("f(x)")
            self.puntos = ax.scatter([], [], s=28, color=NARANJA, edgecolor="white",
                                     lw=0.6, zorder=3, label="Individuos")
            self.mejor, = ax.plot([], [], "*", ms=16, color="black", zorder=4,
                                  label="Mejor de la generación")
        elif self.n == 2:
            g1 = np.linspace(c["x_min"][0], c["x_max"][0], 220)
            g2 = np.linspace(c["x_min"][1], c["x_max"][1], 220)
            X, Y = np.meshgrid(g1, g2)
            Z = np.array([[self.f(np.array([a, b])) for a, b in zip(fa, fb)]
                          for fa, fb in zip(X, Y)])
            cs = ax.contourf(X, Y, Z, levels=30, cmap="Blues_r" if c["tipo"] == "min" else "Blues",
                             zorder=1)
            self.fig.colorbar(cs, ax=ax, fraction=0.04, pad=0.01, label="f(x1, x2)")
            ax.set_xlabel("x1")
            ax.set_ylabel("x2")
            self.puntos = ax.scatter([], [], s=26, color=NARANJA, edgecolor="white",
                                     lw=0.6, zorder=3, label="Individuos")
            self.mejor, = ax.plot([], [], "*", ms=17, color=AMARILLO, markeredgecolor="black",
                                  zorder=4, label="Mejor de la generación")
            ax.set_xlim(c["x_min"][0], c["x_max"][0])
            ax.set_ylim(c["x_min"][1], c["x_max"][1])
        else:
            # 3 o mas variables: cada columna es una variable, cada punto un individuo
            ax.set_xlim(0.4, self.n + 0.6)
            ax.set_ylim(min(c["x_min"]), max(c["x_max"]))
            ax.set_xticks(range(1, self.n + 1))
            ax.set_xticklabels([f"x{i}" for i in range(1, self.n + 1)])
            ax.set_ylabel("Valor de la variable")
            if c.get("x_opt"):
                ax.plot(range(1, self.n + 1), c["x_opt"], "_", ms=30, mew=2, color="black",
                        label="Óptimo (libro)")
            self.puntos = ax.scatter([], [], s=14, color=NARANJA, alpha=0.6, zorder=3,
                                     label="Individuos")
            self.mejor, = ax.plot([], [], "*-", ms=12, color=AZUL, lw=1, zorder=4,
                                  label="Mejor de la generación")
        if self.n == 2:
            ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
        else:
            ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8)
        ax.grid(alpha=0.25)

    def dibujar_evolucion(self):
        ax, r = self.ax_ev, self.res
        gens = np.arange(len(r["hist_mejor"]))
        ax.plot(gens, r["hist_media"], color=GRIS, lw=1.2, label="Media de la población")
        ax.plot(gens, r["hist_mejor_absoluto"], color=AZUL, lw=2.5, label="Mejor absoluto")
        ax.plot(gens, r["hist_mejor"], color=NARANJA, lw=1, ls="--", label="Mejor de la generación")
        if self.c["optimo"] is not None:
            ax.axhline(self.c["optimo"], color="black", ls=":", lw=0.9, label="Óptimo (libro)")
        self.linea_gen = ax.axvline(0, color="black", lw=1.2)
        ax.set_xlabel("Generación")
        ax.set_ylabel("f(x)")
        ax.set_xlim(0, self.num_gen)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(1.01, 1))

    # -------------------------------------------------------------- controles
    def crear_controles(self):
        ax_slider = self.fig.add_axes([0.16, 0.075, 0.68, 0.03])
        self.slider = Slider(ax_slider, "Generación", 0, self.num_gen, valinit=0, valstep=1,
                             color=AZUL)
        self.slider.on_changed(lambda v: self.actualizar(int(v), desde_slider=True))

        botones = [("|<", lambda e: self.ir_a(0)),
                   ("<", lambda e: self.ir_a(self.gen - 1)),
                   ("Play / Pausa", lambda e: self.play_pausa()),
                   (">", lambda e: self.ir_a(self.gen + 1)),
                   (">|", lambda e: self.ir_a(self.num_gen))]
        self.botones = []
        x = 0.25
        for texto, accion in botones:
            ancho = 0.16 if "Play" in texto else 0.07
            b = Button(self.fig.add_axes([x, 0.015, ancho, 0.045]), texto)
            b.on_clicked(accion)
            self.botones.append(b)
            x += ancho + 0.015

        self.timer = self.fig.canvas.new_timer(interval=150)
        self.timer.add_callback(self.paso_automatico)
        self.fig.canvas.mpl_connect("key_press_event", self.tecla)

    def ir_a(self, g):
        g = int(np.clip(g, 0, self.num_gen))
        self.slider.set_val(g)  # esto llama a actualizar()

    def play_pausa(self):
        self.reproduciendo = not self.reproduciendo
        if self.reproduciendo:
            if self.gen >= self.num_gen:
                self.ir_a(0)
            self.timer.start()
        else:
            self.timer.stop()

    def paso_automatico(self):
        if self.gen >= self.num_gen:
            self.reproduciendo = False
            self.timer.stop()
        else:
            self.ir_a(self.gen + 1)

    def tecla(self, evento):
        if evento.key == "right":
            self.ir_a(self.gen + 1)
        elif evento.key == "left":
            self.ir_a(self.gen - 1)
        elif evento.key == " ":
            self.play_pausa()

    # ------------------------------------------------------------ actualizar
    def actualizar(self, g, desde_slider=False):
        self.gen = g
        p, fv = self.pobs[g], self.fvals[g]
        i_mejor = int(np.argmax(fv) if self.c["tipo"] == "max" else np.argmin(fv))

        if self.n == 1:
            self.puntos.set_offsets(np.column_stack([p[:, 0], fv]))
            self.mejor.set_data([p[i_mejor, 0]], [fv[i_mejor]])
        elif self.n == 2:
            self.puntos.set_offsets(p[:, :2])
            self.mejor.set_data([p[i_mejor, 0]], [p[i_mejor, 1]])
        else:
            cols = np.tile(np.arange(1, self.n + 1), len(p))
            jitter = (np.random.default_rng(g).random(len(cols)) - 0.5) * 0.3
            self.puntos.set_offsets(np.column_stack([cols + jitter, p.ravel()]))
            self.mejor.set_data(np.arange(1, self.n + 1), p[i_mejor])

        self.linea_gen.set_xdata([g, g])
        self.ax.set_title(f"Generación {g} de {self.num_gen}   |   mejor de la generación: "
                          f"f = {fv[i_mejor]:.6f}   |   media: {fv.mean():.4f}", fontsize=9.5)
        self.fig.canvas.draw_idle()
        return self.puntos, self.mejor, self.linea_gen

    def guardar_gif(self, archivo, fps=8):
        anim = FuncAnimation(self.fig, lambda g: self.actualizar(g), frames=self.num_gen + 1,
                             blit=False)
        anim.save(archivo, writer=PillowWriter(fps=fps))


def main():
    p = argparse.ArgumentParser(description="Visualiza el AG generacion por generacion")
    p.add_argument("funcion", choices=TODAS)
    p.add_argument("--n", type=int, default=None, help="numero de variables (rastrigin, michalewicz, schwefel)")
    p.add_argument("--tam_pob", type=int, default=50)
    p.add_argument("--num_gen", type=int, default=60)
    p.add_argument("--prob_cruce", type=float, default=0.6)
    p.add_argument("--prob_mut", type=float, default=0.05)
    p.add_argument("--TOL", type=float, default=0.001, help="solo Proyecto 1")
    p.add_argument("--cruce", default="sbx", help="solo Proyecto 2: un_punto, uniforme, aritmetico, sbx")
    p.add_argument("--sin_elitismo", action="store_true")
    p.add_argument("--semilla", type=int, default=None)
    p.add_argument("--gif", default=None, help="guardar la animacion en este archivo .gif")
    args = p.parse_args()

    config, res = ejecutar_ag(args)
    tipo = "binario" if PROYECTO == 1 else f"real, cruce {args.cruce}"
    titulo = f"Proyecto {PROYECTO} - {args.funcion} (AG {tipo})"
    print(f"Mejor encontrado: f = {res['mejor_f']:.6f} en x = {np.round(res['mejor_x'], 5)}")

    if args.gif:
        vis = Visualizador(config, res, titulo, interactivo=False)
        vis.guardar_gif(args.gif)
        print(f"Animación guardada en {args.gif}")
    else:
        vis = Visualizador(config, res, titulo, interactivo=True)
        plt.show()


if __name__ == "__main__":
    main()

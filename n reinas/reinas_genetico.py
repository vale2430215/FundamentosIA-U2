#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problema de las 8 Reinas resuelto con un Algoritmo Genético.
Interfaz gráfica en Tkinter (no requiere librerías externas).

Representación del cromosoma:
    Lista de 8 enteros. El gen i indica la FILA de la reina que está en la
    columna i  (ej. [0, 4, 7, 5, 2, 6, 1, 3]).
Aptitud (fitness):
    Número de pares de reinas que NO se atacan. Máximo = 28 (solución).
Operadores:
    Selección por torneo, cruce de un punto, mutación aleatoria de un gen
    y elitismo.
"""

import random
import tkinter as tk
from tkinter import ttk

N = 8
MAX_FIT = N * (N - 1) // 2  # 28 pares posibles


# --------------------------------------------------------------------------
#  Lógica del algoritmo genético
# --------------------------------------------------------------------------
def pares_atacantes(ind):
    """Devuelve la lista de pares (i, j) de columnas cuyas reinas se atacan."""
    pares = []
    for i in range(N):
        for j in range(i + 1, N):
            if ind[i] == ind[j] or abs(ind[i] - ind[j]) == j - i:
                pares.append((i, j))
    return pares


def aptitud(ind):
    return MAX_FIT - len(pares_atacantes(ind))


class AlgoritmoGenetico:
    def __init__(self, tam_poblacion=100, p_cruce=0.9, p_mutacion=0.2,
                 elitismo=2, torneo=3):
        self.tam = tam_poblacion
        self.p_cruce = p_cruce
        self.p_mutacion = p_mutacion
        self.elitismo = min(elitismo, tam_poblacion)
        self.torneo = torneo
        self.generacion = 0
        self.poblacion = [[random.randrange(N) for _ in range(N)]
                          for _ in range(self.tam)]
        self.evaluar()

    def evaluar(self):
        self.fits = [aptitud(ind) for ind in self.poblacion]
        self.orden = sorted(range(self.tam), key=lambda k: self.fits[k],
                            reverse=True)
        self.mejor = list(self.poblacion[self.orden[0]])
        self.mejor_fit = self.fits[self.orden[0]]
        self.promedio = sum(self.fits) / self.tam
        self.peor_fit = self.fits[self.orden[-1]]

    def seleccion(self):
        """Selección por torneo."""
        candidatos = random.sample(range(self.tam), min(self.torneo, self.tam))
        ganador = max(candidatos, key=lambda k: self.fits[k])
        return self.poblacion[ganador]

    def siguiente_generacion(self):
        nueva = [list(self.poblacion[k]) for k in self.orden[:self.elitismo]]
        while len(nueva) < self.tam:
            p1, p2 = self.seleccion(), self.seleccion()
            if random.random() < self.p_cruce:
                corte = random.randint(1, N - 1)
                h1 = p1[:corte] + p2[corte:]
                h2 = p2[:corte] + p1[corte:]
            else:
                h1, h2 = list(p1), list(p2)
            for h in (h1, h2):
                if random.random() < self.p_mutacion:
                    h[random.randrange(N)] = random.randrange(N)
            nueva.append(h1)
            if len(nueva) < self.tam:
                nueva.append(h2)
        self.poblacion = nueva
        self.generacion += 1
        self.evaluar()

    @property
    def resuelto(self):
        return self.mejor_fit == MAX_FIT


# --------------------------------------------------------------------------
#  Interfaz gráfica
# --------------------------------------------------------------------------
class App:
    CELDA = 64
    CLARO = "#f0d9b5"
    OSCURO = "#b58863"

    def __init__(self, root):
        self.root = root
        root.title("Problema de las 8 Reinas - Algoritmo Genético")
        self.ag = None
        self.corriendo = False
        self.after_id = None
        self.hist_mejor = []
        self.hist_prom = []
        self.mejor_visto = -1

        self._crear_widgets()
        self.reiniciar()

    # ---------------------------- construcción ----------------------------
    def _crear_widgets(self):
        izq = ttk.Frame(self.root, padding=8)
        izq.grid(row=0, column=0, sticky="n")
        der = ttk.Frame(self.root, padding=8)
        der.grid(row=0, column=1, sticky="nsew")
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- Tablero ---
        ttk.Label(izq, text="Mejor individuo de la generación",
                  font=("Segoe UI", 11, "bold")).pack()
        lado = self.CELDA * N
        self.tablero = tk.Canvas(izq, width=lado, height=lado,
                                 highlightthickness=1,
                                 highlightbackground="#555")
        self.tablero.pack(pady=4)

        self.lbl_estado = ttk.Label(izq, text="", font=("Segoe UI", 10))
        self.lbl_estado.pack()

        # --- Parámetros ---
        marco = ttk.LabelFrame(izq, text="Parámetros", padding=6)
        marco.pack(fill="x", pady=6)
        self.v_pob = tk.IntVar(value=200)
        self.v_cruce = tk.DoubleVar(value=0.9)
        self.v_mut = tk.DoubleVar(value=0.8)
        self.v_elite = tk.IntVar(value=1)
        self.v_torneo = tk.IntVar(value=2)
        self.v_max = tk.IntVar(value=500)
        self.v_vel = tk.IntVar(value=150)

        filas = [
            ("Población", self.v_pob, 10, 1000, 10),
            ("Prob. cruce", self.v_cruce, 0.0, 1.0, 0.05),
            ("Prob. mutación", self.v_mut, 0.0, 1.0, 0.05),
            ("Elitismo", self.v_elite, 0, 20, 1),
            ("Tamaño torneo", self.v_torneo, 2, 10, 1),
            ("Máx. generaciones", self.v_max, 10, 10000, 10),
            ("Pausa entre épocas (ms)", self.v_vel, 0, 2000, 10),
        ]
        for r, (txt, var, lo, hi, inc) in enumerate(filas):
            ttk.Label(marco, text=txt).grid(row=r, column=0, sticky="w",
                                            padx=2, pady=1)
            ttk.Spinbox(marco, textvariable=var, from_=lo, to=hi,
                        increment=inc, width=8).grid(row=r, column=1, padx=4)

        # --- Botones ---
        bt = ttk.Frame(izq)
        bt.pack(fill="x", pady=4)
        self.btn_inicio = ttk.Button(bt, text="▶ Iniciar", command=self.alternar)
        self.btn_inicio.grid(row=0, column=0, padx=2)
        ttk.Button(bt, text="⏭ Paso", command=self.paso).grid(row=0, column=1,
                                                              padx=2)
        ttk.Button(bt, text="⟲ Reiniciar", command=self.reiniciar).grid(
            row=0, column=2, padx=2)

        # --- Gráfica ---
        ttk.Label(der, text="Evolución de la aptitud por época",
                  font=("Segoe UI", 11, "bold")).pack()
        self.grafica = tk.Canvas(der, width=520, height=230, bg="white",
                                 highlightthickness=1,
                                 highlightbackground="#555")
        self.grafica.pack(fill="x", pady=4)

        # --- Población (top) ---
        ttk.Label(der, text="Mejores individuos de la población actual",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.tabla = ttk.Treeview(der, columns=("pos", "crom", "fit"),
                                  show="headings", height=6)
        self.tabla.heading("pos", text="#")
        self.tabla.heading("crom", text="Cromosoma (fila de cada columna)")
        self.tabla.heading("fit", text="Aptitud")
        self.tabla.column("pos", width=35, anchor="center")
        self.tabla.column("crom", width=300, anchor="center")
        self.tabla.column("fit", width=70, anchor="center")
        self.tabla.pack(fill="x", pady=4)

        # --- Registro ---
        ttk.Label(der, text="Registro de épocas",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        cont = ttk.Frame(der)
        cont.pack(fill="both", expand=True)
        self.log = tk.Text(cont, height=10, width=70, state="disabled",
                           font=("Consolas", 9), bg="#fafafa")
        sb = ttk.Scrollbar(cont, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.log.tag_configure("mejora", foreground="#0a7a2f",
                               font=("Consolas", 9, "bold"))
        self.log.tag_configure("exito", foreground="#ffffff",
                               background="#0a7a2f",
                               font=("Consolas", 9, "bold"))

        self.grafica.bind("<Configure>", lambda e: self.dibujar_grafica())

    # ------------------------------ control -------------------------------
    def _leer_parametros(self):
        def seguro(var, tipo, defecto):
            try:
                return tipo(var.get())
            except (tk.TclError, ValueError):
                return defecto
        return dict(
            tam_poblacion=max(2, seguro(self.v_pob, int, 100)),
            p_cruce=min(1.0, max(0.0, seguro(self.v_cruce, float, 0.9))),
            p_mutacion=min(1.0, max(0.0, seguro(self.v_mut, float, 0.2))),
            elitismo=max(0, seguro(self.v_elite, int, 2)),
            torneo=max(2, seguro(self.v_torneo, int, 3)),
        )

    def reiniciar(self):
        self._detener()
        self.ag = AlgoritmoGenetico(**self._leer_parametros())
        self.hist_mejor = [self.ag.mejor_fit]
        self.hist_prom = [self.ag.promedio]
        self.mejor_visto = self.ag.mejor_fit
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._escribir_log(self._linea_log(), "mejora")
        self.actualizar_vista()

    def alternar(self):
        if self.corriendo:
            self._detener()
        else:
            if self.ag.resuelto or self.ag.generacion >= self._max_gen():
                self.reiniciar()
            self.corriendo = True
            self.btn_inicio.config(text="⏸ Pausar")
            self._ciclo()

    def _detener(self):
        self.corriendo = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.btn_inicio.config(text="▶ Iniciar")

    def _max_gen(self):
        try:
            return int(self.v_max.get())
        except (tk.TclError, ValueError):
            return 500

    def paso(self):
        if self.corriendo or self.ag.resuelto:
            return
        self._una_generacion()

    def _ciclo(self):
        if not self.corriendo:
            return
        self._una_generacion()
        if self.ag.resuelto or self.ag.generacion >= self._max_gen():
            self._detener()
            self.actualizar_vista()
            return
        try:
            pausa = max(0, int(self.v_vel.get()))
        except (tk.TclError, ValueError):
            pausa = 150
        self.after_id = self.root.after(pausa, self._ciclo)

    def _una_generacion(self):
        self.ag.siguiente_generacion()
        self.hist_mejor.append(self.ag.mejor_fit)
        self.hist_prom.append(self.ag.promedio)
        if self.ag.resuelto:
            self._escribir_log(self._linea_log() + "  ¡SOLUCIÓN ENCONTRADA!",
                               "exito")
        elif self.ag.mejor_fit > self.mejor_visto:
            self._escribir_log(self._linea_log(), "mejora")
        else:
            self._escribir_log(self._linea_log())
        self.mejor_visto = max(self.mejor_visto, self.ag.mejor_fit)
        self.actualizar_vista()

    # ------------------------------- vista --------------------------------
    def _linea_log(self):
        ag = self.ag
        return (f"Época {ag.generacion:4d} | Mejor {ag.mejor_fit:2d}/{MAX_FIT}"
                f" | Prom {ag.promedio:5.2f} | Peor {ag.peor_fit:2d}"
                f" | {ag.mejor}")

    def _escribir_log(self, texto, tag=None):
        self.log.configure(state="normal")
        if tag:
            self.log.insert("end", texto + "\n", tag)
        else:
            self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def actualizar_vista(self):
        self.dibujar_tablero()
        self.dibujar_grafica()
        self.actualizar_tabla()
        ag = self.ag
        if ag.resuelto:
            self.lbl_estado.config(
                text=f"✔ Solución en la época {ag.generacion}", foreground="#0a7a2f")
        else:
            self.lbl_estado.config(
                text=(f"Época {ag.generacion} | Aptitud {ag.mejor_fit}/{MAX_FIT}"
                      f" | Pares en conflicto: {MAX_FIT - ag.mejor_fit}"),
                foreground="#000000")

    def dibujar_tablero(self):
        c = self.tablero
        c.delete("all")
        s = self.CELDA
        ind = self.ag.mejor
        pares = pares_atacantes(ind)
        en_conflicto = {i for p in pares for i in p}

        for f in range(N):
            for col in range(N):
                color = self.CLARO if (f + col) % 2 == 0 else self.OSCURO
                c.create_rectangle(col * s, f * s, (col + 1) * s, (f + 1) * s,
                                   fill=color, outline="")
        # líneas de ataque
        for i, j in pares:
            c.create_line(i * s + s / 2, ind[i] * s + s / 2,
                          j * s + s / 2, ind[j] * s + s / 2,
                          fill="#d62728", width=2, dash=(4, 3))
        # reinas
        for col, fila in enumerate(ind):
            cx, cy = col * s + s / 2, fila * s + s / 2
            ok = col not in en_conflicto
            c.create_oval(cx - 22, cy - 22, cx + 22, cy + 22,
                          fill="#2ca02c" if ok else "#d62728",
                          outline="white", width=2)
            c.create_text(cx, cy - 1, text="♛", font=("Segoe UI Symbol", 26),
                          fill="white")

    def dibujar_grafica(self):
        g = self.grafica
        g.delete("all")
        w = max(g.winfo_width(), 300)
        h = max(g.winfo_height(), 150)
        mi, md, ms, mb = 40, 12, 12, 28
        ancho, alto = w - mi - md, h - ms - mb

        def y_de(v):
            return ms + alto - (v / MAX_FIT) * alto

        # rejilla y etiquetas
        for v in (0, 7, 14, 21, 28):
            y = y_de(v)
            g.create_line(mi, y, w - md, y, fill="#e0e0e0")
            g.create_text(mi - 6, y, text=str(v), anchor="e",
                          font=("Segoe UI", 8))
        g.create_line(mi, ms, mi, ms + alto, fill="#444")
        g.create_line(mi, ms + alto, w - md, ms + alto, fill="#444")
        # meta
        g.create_line(mi, y_de(MAX_FIT), w - md, y_de(MAX_FIT),
                      fill="#2ca02c", dash=(5, 3))

        n = len(self.hist_mejor)
        xmax = max(n - 1, 10)

        def x_de(i):
            return mi + (i / xmax) * ancho

        for i in range(0, xmax + 1, max(1, xmax // 5)):
            g.create_text(x_de(i), ms + alto + 12, text=str(i),
                          font=("Segoe UI", 8))
        g.create_text(mi + ancho / 2, h - 4, text="Época",
                      font=("Segoe UI", 8))

        def trazar(serie, color):
            if len(serie) >= 2:
                pts = []
                for i, v in enumerate(serie):
                    pts += [x_de(i), y_de(v)]
                g.create_line(*pts, fill=color, width=2)
            elif serie:
                g.create_oval(x_de(0) - 2, y_de(serie[0]) - 2,
                              x_de(0) + 2, y_de(serie[0]) + 2, fill=color,
                              outline=color)

        trazar(self.hist_prom, "#1f77b4")
        trazar(self.hist_mejor, "#d62728")
        # leyenda
        g.create_line(mi + 8, ms + 8, mi + 28, ms + 8, fill="#d62728", width=2)
        g.create_text(mi + 32, ms + 8, text="Mejor", anchor="w",
                      font=("Segoe UI", 8))
        g.create_line(mi + 80, ms + 8, mi + 100, ms + 8, fill="#1f77b4",
                      width=2)
        g.create_text(mi + 104, ms + 8, text="Promedio", anchor="w",
                      font=("Segoe UI", 8))

    def actualizar_tabla(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        ag = self.ag
        for pos, k in enumerate(ag.orden[:6], start=1):
            self.tabla.insert("", "end",
                              values=(pos, str(ag.poblacion[k]), ag.fits[k]))


if __name__ == "__main__":
    ventana = tk.Tk()
    App(ventana)
    ventana.mainloop()

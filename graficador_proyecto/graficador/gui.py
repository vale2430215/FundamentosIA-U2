"""Interfaz gráfica (tkinter + matplotlib).

Se escribe la ecuación, el intervalo [x mín, x máx] y se pulsa «Graficar» (o Enter):
a la izquierda aparece el árbol de expresión y a la derecha la curva se va trazando
punto por punto. La lógica vive en `sesion.py`; aquí solo hay widgets.

Los límites aceptan expresiones: -2*pi, sqrt(2), 1/3...

El panel «Biblioteca» permite seleccionar operadores/funciones y generar
ecuaciones aleatorias con altura de árbol configurable.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from .funciones import CONSTANTES, FUNCIONES
from .generador import CATALOGO, GeneradorEcuaciones
from .sesion import ErrorEntrada, Sesion

EJEMPLO = "6.87+11*cos(7.23*x^3)"
INTERVALO_MS = 20          # tiempo entre cuadros de la animación


class Aplicacion:
    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        raiz.title("Intérprete y graficador de expresiones")
        raiz.geometry("1400x860")
        raiz.minsize(1000, 620)
        raiz.columnconfigure(0, weight=1)
        raiz.rowconfigure(1, weight=1)

        self._after_id = None
        self._pausado = False

        # Variables de la biblioteca (checkboxes por operador)
        self._vars_ops: dict[str, tk.BooleanVar] = {}

        self._crear_controles()
        self._crear_biblioteca()
        self._crear_paneles()
        self._crear_estado()

        self.sesion = Sesion(self.ax_arbol, self.ax_graf)
        raiz.protocol("WM_DELETE_WINDOW", self._cerrar)
        raiz.after(150, self.graficar)          # muestra el ejemplo al abrir

    # ---------------------------------------------------------------- widgets
    def _crear_controles(self) -> None:
        barra = ttk.Frame(self.raiz, padding=(10, 8, 10, 4))
        barra.grid(row=0, column=0, sticky="ew")

        fila1 = ttk.Frame(barra)
        fila1.pack(fill="x")
        ttk.Label(fila1, text="y =").pack(side="left")
        self.var_expr = tk.StringVar(value=EJEMPLO)
        self.ent_expr = ttk.Entry(fila1, textvariable=self.var_expr, font="TkFixedFont")
        self.ent_expr.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(fila1, text="Graficar", command=self.graficar).pack(side="left")

        fila2 = ttk.Frame(barra)
        fila2.pack(fill="x", pady=(6, 0))
        self.var_xmin = tk.StringVar(value="-10")
        self.var_xmax = tk.StringVar(value="10")
        self.var_puntos = tk.StringVar(value="20001")
        self.var_vel = tk.DoubleVar(value=20)

        ttk.Label(fila2, text="x mín").pack(side="left")
        ttk.Entry(fila2, textvariable=self.var_xmin, width=9).pack(side="left", padx=(4, 10))
        ttk.Label(fila2, text="x máx").pack(side="left")
        ttk.Entry(fila2, textvariable=self.var_xmax, width=9).pack(side="left", padx=(4, 10))
        ttk.Label(fila2, text="Puntos").pack(side="left")
        ttk.Spinbox(fila2, from_=20, to=25000, increment=100, width=7,
                    textvariable=self.var_puntos).pack(side="left", padx=(4, 10))
        ttk.Label(fila2, text="Velocidad").pack(side="left")
        ttk.Scale(fila2, from_=1, to=40, orient="horizontal", length=130,
                  variable=self.var_vel).pack(side="left", padx=(4, 14))

        self.btn_pausa = ttk.Button(fila2, text="Pausar", command=self.pausar, state="disabled")
        self.btn_pausa.pack(side="left", padx=2)
        ttk.Button(fila2, text="Completar", command=self.completar).pack(side="left", padx=2)
        ttk.Button(fila2, text="Limpiar", command=self.limpiar).pack(side="left", padx=2)
        ttk.Button(fila2, text="Guardar imágenes…", command=self.guardar).pack(side="left", padx=2)
        ttk.Button(fila2, text="Exportar CSV…", command=self.exportar_csv).pack(side="left", padx=2)

        for ent in (self.ent_expr,):
            ent.bind("<Return>", self.graficar)
        for hijo in fila2.winfo_children():
            if isinstance(hijo, (ttk.Entry, ttk.Spinbox)):
                hijo.bind("<Return>", self.graficar)

        ayuda = ("Funciones: " + ", ".join(sorted(FUNCIONES))
                 + "   ·   constantes: " + ", ".join(sorted(CONSTANTES))
                 + "   ·   potencia: ^ o **   ·   multiplicación implícita: 2x, 3(x+1)"
                 + "   ·   módulo: mod(a, b)")
        ttk.Label(barra, text=ayuda, foreground="#666666", wraplength=1350,
                  justify="left").pack(fill="x", pady=(6, 0))

    # ----------------------------------------------------------- biblioteca
    def _crear_biblioteca(self) -> None:
        """Panel colapsable con la biblioteca de operadores y el generador aleatorio."""
        # Marco exterior con borde visual
        outer = ttk.LabelFrame(self.raiz, text=" Biblioteca de operadores ", padding=(8, 4))
        outer.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 2))
        # No expandir verticalmente; los paneles gráficos van en row=2
        self.raiz.rowconfigure(1, weight=0)
        self.raiz.rowconfigure(2, weight=1)

        # ── Columna izquierda: checkboxes de operadores ──────────────────────
        marco_ops = ttk.Frame(outer)
        marco_ops.pack(side="left", padx=(0, 16))

        ttk.Label(marco_ops, text="Operadores disponibles:",
                  font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, columnspan=4,
                                                           sticky="w", pady=(0, 4))

        # Claves activas por defecto (coinciden con CLAVES_DEFECTO del generador)
        defecto = {"suma", "resta", "mult", "pot", "sin", "cos"}
        items = list(CATALOGO.values())
        cols = 3       # checkboxes en 3 columnas
        for idx, entrada in enumerate(items):
            var = tk.BooleanVar(value=(entrada.clave in defecto))
            self._vars_ops[entrada.clave] = var
            fila_cb = (idx // cols) + 1
            col_cb = idx % cols
            cb = ttk.Checkbutton(
                marco_ops, text=f"{entrada.etiqueta}",
                variable=var,
                command=self._actualizar_info_biblioteca,
            )
            cb.grid(row=fila_cb, column=col_cb, sticky="w", padx=6, pady=1)
            if entrada.descripcion:
                cb.bind("<Enter>", lambda e, d=entrada.descripcion: self._mostrar_tooltip(d))

        # ── Columna central: controles del generador ─────────────────────────
        sep = ttk.Separator(outer, orient="vertical")
        sep.pack(side="left", fill="y", padx=8)

        marco_gen = ttk.Frame(outer)
        marco_gen.pack(side="left", padx=(0, 16))

        ttk.Label(marco_gen, text="Generador aleatorio:",
                  font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, columnspan=2,
                                                           sticky="w", pady=(0, 4))

        ttk.Label(marco_gen, text="Altura máx. árbol:").grid(row=1, column=0, sticky="w", pady=2)
        self.var_altura = tk.IntVar(value=4)
        ttk.Spinbox(marco_gen, from_=2, to=8, increment=1, width=5,
                    textvariable=self.var_altura).grid(row=1, column=1, sticky="w", padx=4)

        ttk.Label(marco_gen, text="Prob. usar variable x:").grid(row=2, column=0, sticky="w", pady=2)
        self.var_prob_var = tk.DoubleVar(value=0.6)
        ttk.Scale(marco_gen, from_=0.1, to=1.0, orient="horizontal", length=100,
                  variable=self.var_prob_var).grid(row=2, column=1, sticky="w", padx=4)

        ttk.Label(marco_gen, text="Semilla (vacío=aleatoria):").grid(row=3, column=0, sticky="w", pady=2)
        self.var_semilla = tk.StringVar(value="")
        ttk.Entry(marco_gen, textvariable=self.var_semilla, width=8).grid(
            row=3, column=1, sticky="w", padx=4)

        ttk.Button(marco_gen, text="Generar ecuación aleatoria",
                   command=self.generar_aleatoria).grid(
            row=4, column=0, columnspan=2, pady=(8, 2), sticky="ew")

        # ── Columna derecha: info operadores activos ──────────────────────────
        sep2 = ttk.Separator(outer, orient="vertical")
        sep2.pack(side="left", fill="y", padx=8)

        marco_info = ttk.Frame(outer)
        marco_info.pack(side="left", fill="both", expand=True)

        ttk.Label(marco_info, text="Operadores activos:",
                  font=("TkDefaultFont", 9, "bold")).pack(anchor="w")

        self.txt_biblioteca = tk.Text(
            marco_info, height=5, wrap="word", state="disabled",
            relief="flat", background="#f0f8e8", font=("TkFixedFont", 8))
        self.txt_biblioteca.pack(fill="both", expand=True)
        self.txt_biblioteca.tag_configure("titulo", foreground="#1a6a1a",
                                          font=("TkFixedFont", 8, "bold"))
        self.txt_biblioteca.tag_configure("desc", foreground="#2d4a2d")

        self._actualizar_info_biblioteca()

    def _actualizar_info_biblioteca(self) -> None:
        """Refresca el panel de texto con los operadores actualmente activos."""
        activos = [CATALOGO[k] for k, v in self._vars_ops.items() if v.get()]
        bins = [e for e in activos if e.aridad == 2]
        unis = [e for e in activos if e.aridad == 1]

        lineas: list[tuple[str, str]] = []
        lineas.append(("titulo", f"Binarios ({len(bins)}): "))
        if bins:
            lineas.append(("desc", "  " + "  |  ".join(
                f"{e.simbolo} [{e.descripcion}]" for e in bins) + "\n"))
        else:
            lineas.append(("desc", "  (ninguno)\n"))

        lineas.append(("titulo", f"Unarios ({len(unis)}): "))
        if unis:
            lineas.append(("desc", "  " + "  |  ".join(
                f"{e.simbolo}(x) [{e.descripcion}]" for e in unis) + "\n"))
        else:
            lineas.append(("desc", "  (ninguno)\n"))

        total = len(activos)
        lineas.append(("desc", f"\nTotal activos: {total}  |  "
                       f"Binarios: {len(bins)}  |  Unarios: {len(unis)}\n"))

        self.txt_biblioteca.configure(state="normal")
        self.txt_biblioteca.delete("1.0", "end")
        for tag, txt in lineas:
            self.txt_biblioteca.insert("end", txt, tag)
        self.txt_biblioteca.configure(state="disabled")

    def _mostrar_tooltip(self, texto: str) -> None:
        """Muestra el texto de descripción brevemente en el panel de info."""
        pass  # Se podría implementar un tooltip; por ahora no bloquea nada

    # ---------------------------------------------------------- generador
    def generar_aleatoria(self) -> None:
        """Genera una ecuación aleatoria con los operadores y altura configurados."""
        ops_activos = {k for k, v in self._vars_ops.items() if v.get()}
        if not ops_activos:
            self._escribir(["Selecciona al menos un operador en la biblioteca."], "error")
            return

        semilla_txt = self.var_semilla.get().strip()
        semilla = int(semilla_txt) if semilla_txt.lstrip("-").isdigit() else None

        gen = GeneradorEcuaciones(
            operadores=ops_activos,
            max_altura=self.var_altura.get(),
            prob_variable=self.var_prob_var.get(),
            semilla=semilla,
        )
        expr = gen.generar()
        self.var_expr.set(expr)
        self.graficar()

    # ------------------------------------------------------------ paneles
    def _crear_paneles(self) -> None:
        paned = ttk.PanedWindow(self.raiz, orient="horizontal")
        paned.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)

        marco_a = ttk.Frame(paned)
        marco_g = ttk.Frame(paned)
        paned.add(marco_a, weight=1)
        paned.add(marco_g, weight=1)

        self.fig_arbol = Figure(figsize=(5, 5), constrained_layout=True)
        self.ax_arbol = self.fig_arbol.add_subplot(111)
        self.canvas_arbol = FigureCanvasTkAgg(self.fig_arbol, master=marco_a)
        self.canvas_arbol.get_tk_widget().pack(fill="both", expand=True)

        self.fig_graf = Figure(figsize=(6, 5), constrained_layout=True)
        self.ax_graf = self.fig_graf.add_subplot(111)
        self.canvas_graf = FigureCanvasTkAgg(self.fig_graf, master=marco_g)
        barra = NavigationToolbar2Tk(self.canvas_graf, marco_g)
        barra.update()
        self.canvas_graf.get_tk_widget().pack(fill="both", expand=True)

    def _crear_estado(self) -> None:
        marco = ttk.Frame(self.raiz, padding=(10, 0, 10, 8))
        marco.grid(row=3, column=0, sticky="ew")

        # Panel de estado general
        self.txt_estado = tk.Text(marco, height=3, wrap="word", state="disabled",
                                  relief="flat", background="#f4f4f4")
        self.txt_estado.pack(fill="x")
        self.txt_estado.tag_configure("error", foreground="#b00020")
        self.txt_estado.tag_configure("aviso", foreground="#8a5a00")

        # Panel de métricas de error
        ttk.Separator(marco, orient="horizontal").pack(fill="x", pady=(4, 2))
        lbl = ttk.Label(marco, text="Métricas de error (exacto vs. CSV):",
                        font=("TkDefaultFont", 9, "bold"))
        lbl.pack(anchor="w")
        self.txt_metricas = tk.Text(marco, height=5, wrap="word", state="disabled",
                                    relief="flat", background="#eef4fb")
        self.txt_metricas.pack(fill="x")
        self.txt_metricas.tag_configure("clave", foreground="#1a5276",
                                        font=("TkFixedFont", 9, "bold"))
        self.txt_metricas.tag_configure("val", foreground="#1d3461",
                                        font=("TkFixedFont", 9))
        self._escribir_metricas(["  (Exporta un CSV para calcular las métricas)"])

    # ----------------------------------------------------------------- estado
    def _escribir(self, lineas: list[str], etiqueta: str | None = None) -> None:
        self.txt_estado.configure(state="normal")
        self.txt_estado.delete("1.0", "end")
        for linea in lineas:
            tag = etiqueta
            if etiqueta is None and (linea.startswith(("Sin valores", "División", "La expresión no"))):
                tag = "aviso"
            self.txt_estado.insert("end", linea + "\n", tag or ())
        self.txt_estado.configure(state="disabled")

    def _escribir_metricas(self, lineas: list[str]) -> None:
        self.txt_metricas.configure(state="normal")
        self.txt_metricas.delete("1.0", "end")
        for linea in lineas:
            if linea.strip().startswith("──"):
                self.txt_metricas.insert("end", linea + "\n", "clave")
            else:
                self.txt_metricas.insert("end", linea + "\n", "val")
        self.txt_metricas.configure(state="disabled")

    # ------------------------------------------------------------ animación
    def _cancelar_tic(self) -> None:
        if self._after_id is not None:
            self.raiz.after_cancel(self._after_id)
            self._after_id = None

    def _tic(self) -> None:
        self._after_id = None
        if not self.sesion.activa or self._pausado:
            return
        paso = max(1, int(round(self.var_vel.get())))
        terminada = self.sesion.avanzar(paso)
        self.canvas_graf.draw_idle()
        if terminada:
            self.btn_pausa.configure(state="disabled")
            return
        self._after_id = self.raiz.after(INTERVALO_MS, self._tic)

    # ---------------------------------------------------------------- acciones
    def graficar(self, _evento=None) -> None:
        self._cancelar_tic()
        try:
            info = self.sesion.iniciar(self.var_expr.get(), self.var_xmin.get(),
                                       self.var_xmax.get(), self.var_puntos.get())
        except ErrorEntrada as e:
            self._escribir([str(e)], "error")
            if self.sesion.activa and not self.sesion.animacion.terminada:
                self._pausado = False
                self._tic()                         # reanuda la animación anterior
            return
        self._escribir(info)
        self.canvas_arbol.draw_idle()
        self.canvas_graf.draw_idle()
        self._pausado = False
        self.btn_pausa.configure(text="Pausar", state="normal")
        self._tic()

    def pausar(self) -> None:
        if not self.sesion.activa:
            return
        if self._pausado:
            self._pausado = False
            self.btn_pausa.configure(text="Pausar")
            self._tic()
        else:
            self._pausado = True
            self._cancelar_tic()
            self.btn_pausa.configure(text="Reanudar")

    def completar(self) -> None:
        self._cancelar_tic()
        self.sesion.completar()
        self.canvas_graf.draw_idle()
        self.btn_pausa.configure(text="Pausar", state="disabled")

    def limpiar(self) -> None:
        self._cancelar_tic()
        self.sesion.limpiar()
        self.canvas_arbol.draw_idle()
        self.canvas_graf.draw_idle()
        self.btn_pausa.configure(text="Pausar", state="disabled")
        self._escribir([])

    def exportar_csv(self) -> None:
        """Exporta los puntos válidos a CSV y muestra las métricas de error."""
        if not self.sesion.activa:
            self._escribir(["Primero grafica una expresión."], "error")
            return
        self.completar()                        # asegura que la curva esté completa
        ruta = filedialog.asksaveasfilename(
            title="Exportar puntos como CSV", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")], initialfile="puntos.csv")
        if not ruta:
            return
        try:
            metricas = self.sesion.exportar_csv(ruta)
        except Exception as exc:  # noqa: BLE001
            self._escribir([f"Error al exportar: {exc}"], "error")
            return
        self._escribir([f"CSV guardado: {ruta}"])
        self._escribir_metricas(metricas.lineas())

    def guardar(self) -> None:
        if not self.sesion.activa:
            self._escribir(["Primero grafica una expresión."], "error")
            return
        self.completar()
        ruta = filedialog.asksaveasfilename(
            title="Guardar imágenes (se crean dos archivos)", defaultextension=".png",
            filetypes=[("PNG", "*.png")], initialfile="expresion.png")
        if not ruta:
            return
        base = ruta[:-4] if ruta.lower().endswith(".png") else ruta
        self.fig_graf.savefig(base + "_grafica.png", dpi=150)
        self.fig_arbol.savefig(base + "_arbol.png", dpi=150)
        self._escribir([f"Guardado: {base}_grafica.png y {base}_arbol.png"])

    def _cerrar(self) -> None:
        self._cancelar_tic()
        self.raiz.destroy()


def main() -> None:
    raiz = tk.Tk()
    Aplicacion(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()

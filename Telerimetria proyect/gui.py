"""
gui.py
------
Interfaz gráfica del monitor de rendimiento para videojuegos.

Estética:
    - Fondo degradado de negro (arriba) a morado (abajo).
    - Bordes / contornos en morado neón.
    - Botones de navegación para elegir qué componente ver:
      Resumen general, RAM, Disco, Procesador, Tarjeta gráfica.
"""

import tkinter as tk
from tkinter import font as tkfont

import hardware_monitor as hw

# --------------------------------------------------------------------------
# Paleta de colores
# --------------------------------------------------------------------------
COLOR_TOP = (5, 0, 10)        # negro con un toque de morado, arriba del degradado
COLOR_BOTTOM = (90, 0, 140)   # morado intenso, abajo del degradado
NEON_PURPLE = "#c400ff"
NEON_PURPLE_SOFT = "#8a2be2"
PANEL_BG = "#0d0014"
TEXT_COLOR = "#f2e9ff"
SUBTEXT_COLOR = "#b98cff"
ALERT_COLOR = "#ff2e63"
OK_COLOR = "#39ff8f"
WARN_COLOR = "#ffb703"

REFRESH_MS = 1500  # frecuencia de actualización de datos


def _lerp(a, b, t):
    return a + (b - a) * t


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in rgb)


# --------------------------------------------------------------------------
# Fondo degradado (Canvas)
# --------------------------------------------------------------------------
class GradientBackground(tk.Canvas):
    def __init__(self, parent, top_color=COLOR_TOP, bottom_color=COLOR_BOTTOM, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.top_color = top_color
        self.bottom_color = bottom_color
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1 or height <= 1:
            return
        steps = max(height, 2)
        for i in range(steps):
            t = i / steps
            color = _rgb_to_hex((
                _lerp(self.top_color[0], self.bottom_color[0], t),
                _lerp(self.top_color[1], self.bottom_color[1], t),
                _lerp(self.top_color[2], self.bottom_color[2], t),
            ))
            self.create_line(0, i, width, i, fill=color, tags="gradient")
        self.tag_lower("gradient")


# --------------------------------------------------------------------------
# Barra de progreso neón
# --------------------------------------------------------------------------
class NeonProgressBar(tk.Canvas):
    def __init__(self, parent, width=420, height=26, **kwargs):
        super().__init__(parent, width=width, height=height, bg=PANEL_BG,
                          highlightthickness=1, highlightbackground=NEON_PURPLE_SOFT, **kwargs)
        self._bar_width = width
        self._bar_height = height
        self._bar = self.create_rectangle(0, 0, 0, height, width=0, fill=NEON_PURPLE)
        self._label = self.create_text(width / 2, height / 2, text="0.0%",
                                        fill=TEXT_COLOR, font=("Segoe UI", 10, "bold"))

    def set_percent(self, percent, alert=False):
        if percent is None:
            self.itemconfig(self._label, text="N/D")
            self.coords(self._bar, 0, 0, 0, self._bar_height)
            return
        percent = max(0.0, min(100.0, float(percent)))
        fill_w = self._bar_width * percent / 100.0
        color = ALERT_COLOR if alert else NEON_PURPLE
        self.coords(self._bar, 0, 0, fill_w, self._bar_height)
        self.itemconfig(self._bar, fill=color)
        self.itemconfig(self._label, text=f"{percent:.1f}%")
        self.tag_raise(self._label)


# --------------------------------------------------------------------------
# Botón estilo neón
# --------------------------------------------------------------------------
def make_neon_button(parent, text, command, active=False):
    btn = tk.Button(
        parent, text=text, command=command,
        font=("Segoe UI", 10, "bold"),
        bg=NEON_PURPLE if active else "#1a0026",
        fg="#000000" if active else NEON_PURPLE,
        activebackground=NEON_PURPLE,
        activeforeground="#000000",
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=NEON_PURPLE,
        highlightcolor=NEON_PURPLE,
        padx=14, pady=8,
        cursor="hand2",
    )
    return btn


# --------------------------------------------------------------------------
# Aplicación principal
# --------------------------------------------------------------------------
class GameMonitorApp(tk.Tk):
    VIEWS = ["overview", "ram", "disk", "cpu", "gpu"]
    VIEW_LABELS = {
        "overview": "Resumen general",
        "ram": "RAM",
        "disk": "Disco",
        "cpu": "Procesador",
        "gpu": "Tarjeta gráfica",
    }

    def __init__(self):
        super().__init__()
        self.title("GameHW Monitor — Telemetría de Hardware")
        self.geometry("760x560")
        self.minsize(680, 520)
        self.configure(bg=COLOR_TOP[0] and "#000000" or "#000000")

        self.current_view = "overview"
        self.widget_refs = {}
        self.nav_buttons = {}

        self._build_layout()
        self._render_view(self.current_view)
        self._update_loop()

    # ---------------------------------------------------------------- UI --
    def _build_layout(self):
        # Fondo degradado ocupa toda la ventana
        self.bg = GradientBackground(self)
        self.bg.pack(fill="both", expand=True)

        # Contenedor con borde neón, "flotando" sobre el fondo
        self.outer = tk.Frame(self.bg, bg=PANEL_BG, highlightthickness=3,
                               highlightbackground=NEON_PURPLE, highlightcolor=NEON_PURPLE)
        self.bg.create_window(20, 20, anchor="nw", window=self.outer,
                               width=1, height=1, tags="outer_window")
        self.bg.bind("<Configure>", self._resize_outer, add="+")

        # Encabezado
        header = tk.Frame(self.outer, bg=PANEL_BG)
        header.pack(fill="x", padx=16, pady=(14, 6))
        title_font = tkfont.Font(family="Segoe UI", size=15, weight="bold")
        tk.Label(header, text="⚡ GameHW Monitor", font=title_font,
                 bg=PANEL_BG, fg=NEON_PURPLE).pack(side="left")
        tk.Label(header, text="Rendimiento de componentes en tiempo real",
                 font=("Segoe UI", 9), bg=PANEL_BG, fg=SUBTEXT_COLOR).pack(side="left", padx=12)

        # Barra de navegación
        nav = tk.Frame(self.outer, bg=PANEL_BG)
        nav.pack(fill="x", padx=16, pady=(0, 10))
        for view in self.VIEWS:
            btn = make_neon_button(
                nav, self.VIEW_LABELS[view],
                command=lambda v=view: self._on_nav_click(v),
                active=(view == self.current_view),
            )
            btn.pack(side="left", padx=(0, 8))
            self.nav_buttons[view] = btn

        # Panel de alertas
        self.alert_panel = tk.Label(
            self.outer, text="Sin alertas por el momento.",
            bg=PANEL_BG, fg=OK_COLOR, font=("Segoe UI", 9, "bold"),
            wraplength=680, justify="left", anchor="w",
        )
        self.alert_panel.pack(fill="x", padx=16, pady=(0, 8))

        # Separador
        sep = tk.Frame(self.outer, bg=NEON_PURPLE_SOFT, height=1)
        sep.pack(fill="x", padx=16, pady=(0, 10))

        # Contenido (cambia según la vista)
        self.content = tk.Frame(self.outer, bg=PANEL_BG)
        self.content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _resize_outer(self, event):
        w = max(event.width - 40, 100)
        h = max(event.height - 40, 100)
        self.bg.coords("outer_window", 20, 20)
        self.bg.itemconfig("outer_window", width=w, height=h)

    def _on_nav_click(self, view):
        self.current_view = view
        for v, btn in self.nav_buttons.items():
            active = v == view
            btn.configure(
                bg=NEON_PURPLE if active else "#1a0026",
                fg="#000000" if active else NEON_PURPLE,
            )
        self._render_view(view)

    # ------------------------------------------------------------- Vistas --
    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()
        self.widget_refs = {}

    def _section_title(self, parent, text):
        tk.Label(parent, text=text, bg=PANEL_BG, fg=NEON_PURPLE,
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 10))

    def _labeled_bar(self, parent, label_text):
        row = tk.Frame(parent, bg=PANEL_BG)
        row.pack(fill="x", pady=6)
        tk.Label(row, text=label_text, bg=PANEL_BG, fg=TEXT_COLOR,
                  font=("Segoe UI", 10), width=16, anchor="w").pack(side="left")
        bar = NeonProgressBar(row, width=380, height=22)
        bar.pack(side="left", padx=8)
        return bar

    def _info_label(self, parent, text=""):
        lbl = tk.Label(parent, text=text, bg=PANEL_BG, fg=SUBTEXT_COLOR,
                        font=("Segoe UI", 9), justify="left", anchor="w")
        lbl.pack(anchor="w", pady=2)
        return lbl

    def _render_view(self, view):
        self._clear_content()
        if view == "overview":
            self._build_overview()
        elif view == "ram":
            self._build_ram_view()
        elif view == "disk":
            self._build_disk_view()
        elif view == "cpu":
            self._build_cpu_view()
        elif view == "gpu":
            self._build_gpu_view()

    def _build_overview(self):
        self._section_title(self.content, "Resumen general del sistema")
        self.widget_refs["ov_ram"] = self._labeled_bar(self.content, "RAM")
        self.widget_refs["ov_disk"] = self._labeled_bar(self.content, "Disco")
        self.widget_refs["ov_cpu"] = self._labeled_bar(self.content, "Procesador")
        self.widget_refs["ov_gpu"] = self._labeled_bar(self.content, "Tarjeta gráfica")
        self.widget_refs["ov_info"] = self._info_label(
            self.content, "Selecciona un botón arriba para ver el detalle de cada componente.")

    def _build_ram_view(self):
        self._section_title(self.content, "Memoria RAM")
        self.widget_refs["ram_bar"] = self._labeled_bar(self.content, "Uso RAM")
        self.widget_refs["ram_info"] = self._info_label(self.content)

    def _build_disk_view(self):
        self._section_title(self.content, "Disco duro")
        self.widget_refs["disk_bar"] = self._labeled_bar(self.content, "Uso disco")
        self.widget_refs["disk_info"] = self._info_label(self.content)

    def _build_cpu_view(self):
        self._section_title(self.content, "Procesador (CPU)")
        self.widget_refs["cpu_bar"] = self._labeled_bar(self.content, "Uso general")
        self.widget_refs["cpu_info"] = self._info_label(self.content)
        tk.Label(self.content, text="Uso por núcleo:", bg=PANEL_BG, fg=NEON_PURPLE,
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 4))
        cores_frame = tk.Frame(self.content, bg=PANEL_BG)
        cores_frame.pack(fill="both", expand=True)
        self.widget_refs["cpu_cores_frame"] = cores_frame
        self.widget_refs["cpu_core_bars"] = []

    def _build_gpu_view(self):
        self._section_title(self.content, "Tarjeta gráfica (GPU)")
        gpu_frame = tk.Frame(self.content, bg=PANEL_BG)
        gpu_frame.pack(fill="both", expand=True)
        self.widget_refs["gpu_frame"] = gpu_frame
        self.widget_refs["gpu_widgets"] = []

    # -------------------------------------------------------- Actualizar --
    def _update_loop(self):
        try:
            data = hw.collect_all()
            self._refresh_alerts(data["alerts"])
            self._refresh_current_view(data)
        except Exception as exc:
            self.alert_panel.configure(text=f"Error leyendo hardware: {exc}", fg=ALERT_COLOR)
        finally:
            self.after(REFRESH_MS, self._update_loop)

    def _refresh_alerts(self, alerts):
        if alerts:
            text = "⚠ ALERTA: " + "  |  ".join(alerts)
            self.alert_panel.configure(text=text, fg=ALERT_COLOR)
        else:
            self.alert_panel.configure(text="✓ Todos los componentes en niveles normales.",
                                        fg=OK_COLOR)

    def _refresh_current_view(self, data):
        ram, disk, cpu, gpus = data["ram"], data["disk"], data["cpu"], data["gpus"]
        gpu_alert = any(g["load_percent"] >= hw.THRESHOLDS["gpu"] for g in gpus)
        gpu_percent = gpus[0]["load_percent"] if gpus else None

        if "ov_ram" in self.widget_refs:
            self.widget_refs["ov_ram"].set_percent(ram["percent"], ram["percent"] >= hw.THRESHOLDS["ram"])
            self.widget_refs["ov_disk"].set_percent(disk["percent"], disk["percent"] >= hw.THRESHOLDS["disk"])
            self.widget_refs["ov_cpu"].set_percent(cpu["percent"], cpu["percent"] >= hw.THRESHOLDS["cpu"])
            self.widget_refs["ov_gpu"].set_percent(gpu_percent, gpu_alert)

        if "ram_bar" in self.widget_refs:
            self.widget_refs["ram_bar"].set_percent(ram["percent"], ram["percent"] >= hw.THRESHOLDS["ram"])
            self.widget_refs["ram_info"].configure(
                text=(f"Total: {ram['total_gb']} GB   |   Usada: {ram['used_gb']} GB   |   "
                      f"Disponible: {ram['available_gb']} GB"))

        if "disk_bar" in self.widget_refs:
            self.widget_refs["disk_bar"].set_percent(disk["percent"], disk["percent"] >= hw.THRESHOLDS["disk"])
            self.widget_refs["disk_info"].configure(
                text=(f"Unidad: {disk['path']}   |   Total: {disk['total_gb']} GB   |   "
                      f"Usado: {disk['used_gb']} GB   |   Libre: {disk['free_gb']} GB"))

        if "cpu_bar" in self.widget_refs:
            self.widget_refs["cpu_bar"].set_percent(cpu["percent"], cpu["percent"] >= hw.THRESHOLDS["cpu"])
            temp_txt = f"{cpu['temp_c']} °C" if cpu["temp_c"] is not None else "No disponible en este sistema"
            freq_txt = f"{cpu['freq_mhz']} MHz" if cpu["freq_mhz"] else "N/D"
            self.widget_refs["cpu_info"].configure(
                text=f"Núcleos: {cpu['cores']}   |   Frecuencia: {freq_txt}   |   Temperatura: {temp_txt}")
            self._refresh_cpu_cores(cpu["per_core"])

        if "gpu_frame" in self.widget_refs:
            self._refresh_gpu_view(gpus)

    def _refresh_cpu_cores(self, per_core):
        frame = self.widget_refs["cpu_cores_frame"]
        bars = self.widget_refs["cpu_core_bars"]
        if len(bars) != len(per_core):
            for w in frame.winfo_children():
                w.destroy()
            bars = []
            for i, _ in enumerate(per_core):
                row = tk.Frame(frame, bg=PANEL_BG)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"Núcleo {i}", bg=PANEL_BG, fg=TEXT_COLOR,
                          font=("Segoe UI", 8), width=10, anchor="w").pack(side="left")
                bar = NeonProgressBar(row, width=300, height=14)
                bar.pack(side="left", padx=4)
                bars.append(bar)
            self.widget_refs["cpu_core_bars"] = bars
        for bar, value in zip(bars, per_core):
            bar.set_percent(value, value >= hw.THRESHOLDS["cpu"])

    def _refresh_gpu_view(self, gpus):
        frame = self.widget_refs["gpu_frame"]
        widgets = self.widget_refs["gpu_widgets"]

        if not gpus:
            if not widgets:
                lbl = tk.Label(
                    frame,
                    text=("No se detectó ninguna GPU NVIDIA compatible.\n"
                          "Este monitor usa GPUtil, que depende de 'nvidia-smi'.\n"
                          "En equipos con GPU AMD/Intel o sin drivers NVIDIA, "
                          "esta sección no podrá mostrar datos."),
                    bg=PANEL_BG, fg=SUBTEXT_COLOR, font=("Segoe UI", 9), justify="left")
                lbl.pack(anchor="w", pady=6)
                self.widget_refs["gpu_widgets"] = [lbl]
            return

        # (Re)construir si cambia la cantidad de GPUs detectadas
        if len(widgets) != len(gpus):
            for w in frame.winfo_children():
                w.destroy()
            widgets = []
            for gpu in gpus:
                block = tk.Frame(frame, bg=PANEL_BG)
                block.pack(fill="x", pady=8)
                tk.Label(block, text=gpu["name"], bg=PANEL_BG, fg=NEON_PURPLE,
                          font=("Segoe UI", 10, "bold")).pack(anchor="w")
                load_bar = self._labeled_bar(block, "Uso GPU")
                mem_bar = self._labeled_bar(block, "Uso VRAM")
                info = self._info_label(block)
                widgets.append({"load": load_bar, "mem": mem_bar, "info": info})
            self.widget_refs["gpu_widgets"] = widgets

        for widget_set, gpu in zip(widgets, gpus):
            widget_set["load"].set_percent(gpu["load_percent"], gpu["load_percent"] >= hw.THRESHOLDS["gpu"])
            widget_set["mem"].set_percent(gpu["mem_percent"], False)
            temp_txt = f"{gpu['temp_c']} °C" if gpu["temp_c"] is not None else "N/D"
            widget_set["info"].configure(
                text=(f"VRAM: {gpu['mem_used_mb']:.0f} / {gpu['mem_total_mb']:.0f} MB   |   "
                      f"Temperatura: {temp_txt}"))


def run_app():
    app = GameMonitorApp()
    app.mainloop()

# gui/landing_page.py (v6.0 - Rediseño DOTEMOS)
# Panel de control principal (Dashboard) para gestionar el flujo de trabajo.

import tkinter as tk
from tkinter import ttk
from gui.theme import (
    FONT_TITULO, FONT_SUBTITULO, FONT_NORMAL, COLOR_FONDO_CLARO, COLOR_BLANCO, COLOR_NEGRO, COLOR_FONDO_MEDIO,
    COLOR_PRIMARIO, COLOR_SECUNDARIO, COLOR_TARJETA
)

class LandingPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=40)
        self.controller = controller
        
        # El dashboard usa el fondo claro
        style = ttk.Style()
        style.configure("Dashboard.TFrame", background=COLOR_FONDO_CLARO)
        self.configure(style="Dashboard.TFrame")

        # --- Header de Bienvenida ---
        header_frame = ttk.Frame(self, style="Dashboard.TFrame")
        header_frame.pack(fill='x', pady=(0, 30))

        # Título principal con colores de la empresa
        lbl_welcome = tk.Label(header_frame, text="Bienvenido a DOTEMOS", font=("Helvetica", 28, "bold"), fg=COLOR_PRIMARIO, bg=COLOR_FONDO_CLARO)
        lbl_welcome.pack(anchor='w')
        
        lbl_subtitle = tk.Label(header_frame, text="Sistema de Gestión de Producción Textil", font=("Helvetica", 16), fg=COLOR_NEGRO, bg=COLOR_FONDO_CLARO)
        lbl_subtitle.pack(anchor='w', pady=(5, 0))

        # --- Grilla de Tarjetas (Cards) ---
        cards_container = ttk.Frame(self, style="Dashboard.TFrame")
        cards_container.pack(fill='x', pady=10)
        
        # 4 columnas iguales
        for i in range(4):
            cards_container.columnconfigure(i, weight=1, uniform="card")

        cards_data = [
            ("Gestión de BOM", "Gestionar lista de materiales, productos, operaciones y máquinas.", "BomView", "📦"),
            ("Órdenes de Producción", "Crear, ver y gestionar todas las órdenes de producción.", "OrdersView", "📋"),
            ("Programación de Carga", "Balancear la carga de trabajo y asignar tareas a los operarios.", "SchedulerView", "👥"),
            ("Reportes y Analíticas", "Visualizar programaciones con diagramas de Gantt y KPIs de rendimiento.", "ReportsView", "📊")
        ]

        for i, (title, desc, frame_name, icon) in enumerate(cards_data):
            # Tarjeta blanca con borde sutil
            card = tk.Frame(cards_container, bg=COLOR_TARJETA, padx=20, pady=25, highlightbackground="#E2E8F0", highlightthickness=1)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            
            # Hover effect
            def on_enter(e, c=card):
                c.config(highlightbackground=COLOR_PRIMARIO, highlightthickness=2)
            def on_leave(e, c=card):
                c.config(highlightbackground="#E2E8F0", highlightthickness=1)
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

            # Contenido clickeable
            def on_click(e, f=frame_name):
                self.controller.show_frame(f)

            # Icono circular (simulado con texto)
            icon_lbl = tk.Label(card, text=icon, font=("Helvetica", 42), bg=COLOR_TARJETA, fg=COLOR_PRIMARIO)
            icon_lbl.pack(pady=(0, 15))

            # Título
            title_lbl = tk.Label(card, text=title, font=("Helvetica", 14, "bold"), bg=COLOR_TARJETA, fg=COLOR_NEGRO, wraplength=200, justify="center")
            title_lbl.pack(pady=(0, 10))

            # Descripción
            desc_lbl = tk.Label(card, text=desc, font=("Helvetica", 10), bg=COLOR_TARJETA, fg="#4A5568", wraplength=200, justify="center")
            desc_lbl.pack(expand=True, fill="both")
            
            # Flecha decorativa
            arrow_lbl = tk.Label(card, text="→", font=("Helvetica", 16, "bold"), bg=COLOR_TARJETA, fg=COLOR_PRIMARIO)
            arrow_lbl.pack(side="bottom", pady=(15, 0))

            # Bindings
            for widget in (card, icon_lbl, title_lbl, desc_lbl, arrow_lbl):
                widget.bind("<Button-1>", on_click)
                widget.config(cursor="hand2")


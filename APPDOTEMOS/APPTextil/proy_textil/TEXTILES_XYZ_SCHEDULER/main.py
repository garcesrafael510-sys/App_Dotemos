# main.py (Versión 5.0 - Arquitectura Modular)
# Este es el punto de entrada principal para la aplicación.

import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from gui.landing_page import LandingPage
from gui.bom_view import BomView
from gui.orders_view import OrdersView
from gui.scheduler_view import SchedulerView
from gui.reports_view import ReportsView
from gui.assignment_view import AssignmentView
from gui.operarios_view import OperariosView
from gui.procesos_view import ProcesosView
from gui.maquinas_view import MaquinasView
from gui.configuracion_view import ConfiguracionView
from src.data_loader import data_loader

class MainApplication(ThemedTk):
    """
    Controlador principal de la aplicación.
    Gestiona la ventana principal y la navegación entre las diferentes vistas (frames).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configuración del tema y la ventana principal
        self.set_theme("arc") 
        self.title("DOTEMOS – Sistema de Gestión de Producción Textil")
        self.geometry("1400x850")

        # --- Estado Compartido de la Aplicación ---
        self.df_bom_full = None
        # Cargar mapa de referencias desde la DB (Punto 5 del requerimiento)
        self.referencia_nombre_map = data_loader.obtener_referencia_nombre_map()
        self.programming_results = None # Almacenará los resultados de la programación
        self.shared_balancing_result = None

        from gui.theme import COLOR_PRIMARIO, COLOR_BLANCO, FONT_MENU, COLOR_FONDO_CLARO

        # --- NUEVO DISEÑO (Header, Sidebar y Main Content) ---
        # Header Superior
        self.header = tk.Frame(self, bg=COLOR_PRIMARIO, height=60)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False) # Mantener altura
        
        # Botón Hamburguesa ("3 rayas")
        self.btn_toggle = tk.Button(self.header, text="☰", font=("Helvetica", 18, "bold"), bg=COLOR_PRIMARIO, fg=COLOR_BLANCO, relief="flat", activebackground="#2b6cb0", activeforeground=COLOR_BLANCO, cursor="hand2", command=self.toggle_sidebar)
        self.btn_toggle.pack(side="left", padx=(10, 5))

        # Logo o Nombre en Header
        tk.Label(self.header, text="📦 DOTEMOS", bg=COLOR_PRIMARIO, fg=COLOR_BLANCO, font=("Helvetica", 22, "bold")).pack(side="left", padx=10)
        
        # Usuario a la derecha
        tk.Label(self.header, text="🔔  |  👤 Administrador  ▼", bg=COLOR_PRIMARIO, fg=COLOR_BLANCO, font=FONT_MENU).pack(side="right", padx=20)
        
        # Area Principal (debajo del header)
        self.main_area = tk.Frame(self, bg=COLOR_FONDO_CLARO)
        self.main_area.pack(side="top", fill="both", expand=True)
        
        # Menú Lateral Izquierdo (Sidebar)
        self.sidebar = tk.Frame(self.main_area, bg=COLOR_BLANCO, width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Separador / borde en el sidebar
        tk.Frame(self.sidebar, bg="#E2E8F0", width=1).pack(side="right", fill="y")
        
        # Contenedor principal donde se mostrarán las diferentes vistas (páginas)
        self.container = ttk.Frame(self.main_area)
        self.container.pack(side="left", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Configuración de los botones laterales (almacenados para poder cambiar su color luego si se desea)
        self.sidebar_btns = {}
        menu_items = [
            ("Inicio", "🏠", "LandingPage"),
            ("Gestión de BOM", "📦", "BomView"),
            ("Órdenes de Producción", "📋", "OrdersView"),
            ("Programación de Carga", "📅", "SchedulerView"),
            ("Reportes y Analíticas", "📊", "ReportsView"),
            ("Operarios", "👥", "OperariosView"),
            ("Procesos", "⚙️", "ProcesosView"),
            ("Máquinas", "🖨️", "MaquinasView"),
            ("Configuración", "⚙", "ConfiguracionView")
        ]
        
        tk.Frame(self.sidebar, bg=COLOR_BLANCO, height=20).pack(side="top") # Espacio arriba
        
        for text, icon, frame_name in menu_items:
            # Botones del menú
            btn_text = f" {icon}   {text}"
            bg_color = "#EBF4FF" if frame_name == "LandingPage" else COLOR_BLANCO
            fg_color = COLOR_PRIMARIO if frame_name == "LandingPage" else "#4A5568"
            
            btn = tk.Button(self.sidebar, text=btn_text, anchor="w", font=FONT_MENU, 
                            bg=bg_color, fg=fg_color, relief="flat", activebackground="#EBF4FF",
                            activeforeground=COLOR_PRIMARIO, cursor="hand2", padx=15, pady=8)
            btn.pack(fill="x", pady=2, padx=10)
            if frame_name:
                btn.config(command=lambda f=frame_name: self.show_frame(f))
            self.sidebar_btns[frame_name] = btn

        # Diccionario para mantener una referencia a cada frame/página
        self.frames = {}

        # Crear e inicializar cada una de las páginas de la aplicación
        for F in (LandingPage, BomView, OrdersView, SchedulerView, ReportsView, AssignmentView, OperariosView, ProcesosView, MaquinasView, ConfiguracionView):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Mostrar la página de inicio (LandingPage) al arrancar
        self.show_frame("LandingPage")

    def toggle_sidebar(self):
        """Oculta o muestra totalmente la barra lateral izquierda."""
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y", before=self.container)
            self.sidebar.pack_propagate(False)

    def show_frame(self, page_name):
        """Muestra un frame por su nombre de clase y activa visualmente su botón."""
        
        # --- Update Sidebar Active State ---
        from gui.theme import COLOR_PRIMARIO, COLOR_BLANCO
        for name, btn in self.sidebar_btns.items():
            if name == page_name:
                btn.config(bg="#EBF4FF", fg=COLOR_PRIMARIO)
            else:
                btn.config(bg=COLOR_BLANCO, fg="#4A5568")

        # --- Show Frame ---
        frame = self.frames.get(page_name)
        if frame:
            # Llamar a inicializadores si existen (por ejemplo refrescar listas)
            if hasattr(frame, 'actualizar_lista_ordenes'):
                 frame.actualizar_lista_ordenes()
            if hasattr(frame, 'cargar_datos_historial'):
                 frame.cargar_datos_historial()
            frame.tkraise()

    def show_assignment_view(self, resultado, params=None):
        """Punto 8: Navegación directa a la vista de asignación."""
        view = self.frames.get("AssignmentView")
        if view:
            if params is None:
                sched = self.frames.get("SchedulerView")
                params = {
                    "num_operarios": sched.num_operarios_var.get(),
                    "tiempo_nivel": sched.unidad_nivelacion_var.get()
                }
            view.cargar_datos(resultado, params)
            self.show_frame("AssignmentView")

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()

import tkinter as tk
from tkinter import ttk
from gui.theme import COLOR_PRIMARIO, COLOR_BLANCO, FONT_TITULO, FONT_NORMAL, COLOR_FONDO_CLARO

class ConfiguracionView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text="⚙ Configuración del Sistema", font=FONT_TITULO).pack(anchor='w')
        ttk.Label(header_frame, text="Ajustes generales, usuarios y preferencias.", font=FONT_NORMAL).pack(anchor='w')
        
        # Area principal compartida
        main_content = tk.Frame(self, bg=COLOR_FONDO_CLARO)
        main_content.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Sidebar interna
        self.nav_frame = tk.Frame(main_content, bg=COLOR_BLANCO, width=200)
        self.nav_frame.pack(side='left', fill='y', padx=(0, 20))
        self.nav_frame.pack_propagate(False)
        
        # Area de despliegue
        self.display_frame = tk.Frame(main_content, bg=COLOR_BLANCO, padx=20, pady=20)
        self.display_frame.pack(side='left', fill='both', expand=True)

        self.nav_btns = {}
        opciones = ["General", "Usuarios", "Preferencias", "Base de Datos"]
        
        for op in opciones:
            btn = tk.Button(self.nav_frame, text=op, font=FONT_NORMAL, bg=COLOR_BLANCO, fg="#4A5568", anchor="w", relief="flat", activebackground="#EBF4FF", activeforeground=COLOR_PRIMARIO, cursor="hand2")
            btn.pack(fill="x", pady=5)
            btn.config(command=lambda o=op: self.seleccionar_opcion(o))
            self.nav_btns[op] = btn
            
        self.lbl_titulo = tk.Label(self.display_frame, text="", font=("Helvetica", 16, "bold"), bg=COLOR_BLANCO, fg=COLOR_PRIMARIO)
        self.lbl_titulo.pack(anchor="w", pady=(0, 10))
        
        self.lbl_contenido = tk.Label(self.display_frame, text="", font=FONT_NORMAL, bg=COLOR_BLANCO, fg="#334155")
        self.lbl_contenido.pack(anchor="w")

        self.seleccionar_opcion("General")

    def seleccionar_opcion(self, opcion):
        for nombre, btn in self.nav_btns.items():
            if nombre == opcion:
                btn.config(bg="#EBF4FF", fg=COLOR_PRIMARIO)
            else:
                btn.config(bg=COLOR_BLANCO, fg="#4A5568")
                
        self.lbl_titulo.config(text=f"Ajustes: {opcion}")
        self.lbl_contenido.config(text=f"Aquí se mostrarán las opciones de configuración para {opcion}.\n\n(Funcionalidad en desarrollo...)")

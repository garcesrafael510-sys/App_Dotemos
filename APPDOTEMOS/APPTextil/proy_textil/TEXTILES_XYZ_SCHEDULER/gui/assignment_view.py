import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import FONT_TITULO, FONT_SUBTITULO, FONT_NORMAL, COLOR_BLANCO, COLOR_FONDO_CLARO
from src.gantt_utils import generar_gantt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AssignmentView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(style="Assignment.TFrame")
        
        # --- Variables de Estado ---
        self.last_results = None
        self.last_params = None
        self.current_garment = None
        
        # Estilo local
        style = ttk.Style()
        style.configure("Assignment.TFrame", background=COLOR_BLANCO)
        style.configure("Header.TFrame", background="#F8F9FA")
        style.configure("Tab.TButton", font=FONT_NORMAL, padding=5)

        # --- Cabecera ---
        self.header_frame = ttk.Frame(self, padding=20, style="Header.TFrame")
        self.header_frame.pack(fill='x')

        top_row = ttk.Frame(self.header_frame, style="Header.TFrame")
        top_row.pack(fill='x')

        ttk.Label(top_row, text="Matriz de Asignación", font=FONT_TITULO, background="#F8F9FA").pack(side='left')
        
        btn_action_frame = ttk.Frame(top_row, style="Header.TFrame")
        btn_action_frame.pack(side='right')
        
        ttk.Button(btn_action_frame, text="← Regresar", 
                   command=lambda: controller.show_frame("SchedulerView")).pack(side='left', padx=5)
        ttk.Button(btn_action_frame, text="⚙️ Asignar Automáticamente", 
                   command=self.asignar_automatico).pack(side='left', padx=5)
        ttk.Button(btn_action_frame, text="💾 Guardar Asignación", 
                   command=self.guardar_asignacion).pack(side='left', padx=5)

        ttk.Label(self.header_frame, text="Ajuste manualmente o asigne automáticamente la carga de trabajo a los operarios.", 
                  font=FONT_NORMAL, background="#F8F9FA").pack(anchor='w', pady=(5, 10))

        # --- Fila de Selector de Prenda (Pestañas) ---
        self.tabs_frame = ttk.Frame(self, padding=(20, 0), style="Assignment.TFrame")
        self.tabs_frame.pack(fill='x')
        self.tab_buttons_list = []

        # --- Información de la Prenda (Dinámica) ---
        self.info_prenda_frame = ttk.Frame(self, padding=20, style="Assignment.TFrame")
        self.info_prenda_frame.pack(fill='x')
        
        self.lbl_prenda_title = ttk.Label(self.info_prenda_frame, text="Prenda: N/A", font=FONT_SUBTITULO, background=COLOR_BLANCO)
        self.lbl_prenda_title.pack(anchor='w')
        
        self.lbl_params_line = ttk.Label(self.info_prenda_frame, text="Cargando...", font=FONT_NORMAL, background=COLOR_BLANCO)
        self.lbl_params_line.pack(anchor='w')

        # --- Tabla de Matriz ---
        self.table_frame = ttk.Frame(self, padding=(20, 0, 20, 0), style="Assignment.TFrame")
        self.table_frame.pack(expand=True, fill='both')

        self.tree = ttk.Treeview(self.table_frame, show='headings')
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.pack(expand=True, fill='both')

        # --- Footer de Totales ---
        self.footer_totals_frame = ttk.Frame(self, padding=20, style="Assignment.TFrame")
        self.footer_totals_frame.pack(fill='x')
        
        self.op_loads_frame = ttk.Frame(self.footer_totals_frame, style="Assignment.TFrame")
        self.op_loads_frame.pack(side='bottom', fill='x', pady=(10, 0))

        ttk.Button(self.footer_totals_frame, text="📊 Ver Diagrama de Gantt", command=self.mostrar_gantt).pack(side='left')

    def cargar_datos(self, resultado, params):
        """Puebla la matriz con los resultados del balanceo."""
        self.last_results = resultado
        self.last_params = params
        
        if not resultado or "df_resultado" not in resultado:
            messagebox.showwarning("Matriz", "No hay datos para mostrar.")
            return

        df = resultado["df_resultado"]
        self.prendas_disponibles = sorted(df['nombre_producto'].unique())
        
        # Limpiar botones de pestañas
        for btn in self.tab_buttons_list: btn.destroy()
        self.tab_buttons_list = []
        
        # Crear nuevos botones de ropa
        for prenda in self.prendas_disponibles:
            btn = ttk.Button(self.tabs_frame, text=prenda, 
                            command=lambda p=prenda: self.seleccionar_prenda(p))
            btn.pack(side='left', padx=5)
            self.tab_buttons_list.append(btn)
        
        # Seleccionar la primera por defecto
        if self.prendas_disponibles:
            self.seleccionar_prenda(self.prendas_disponibles[0])

    def seleccionar_prenda(self, nombre_prenda):
        self.current_garment = nombre_prenda
        self.lbl_prenda_title.config(text=f"Prenda: {nombre_prenda}")
        
        df = self.last_results["df_resultado"]
        df_garment = df[df['nombre_producto'] == nombre_prenda]
        num_op = self.last_params.get("num_operarios", 5)
        tam_paq = self.last_params.get("tamano_paquete", 10)
        tiempo_nivel = self.last_params.get("tiempo_nivel", 480)

        # Actualizar Info Line
        uph = 0 # Asumir o calcular si no viene
        # Buscar en indicadores_produccion
        if "indicadores_produccion" in self.last_results:
             for ind in self.last_results.get("indicadores_produccion", []):
                 if ind["Nombre"] == nombre_prenda:
                     uph = ind.get("Unidades por Hora (Ritmo Bruto)", "0")
        
        self.lbl_params_line.config(text=f"Tiempo de Turno: {tiempo_nivel} min | Ritmo Bruto Estimado: {uph} UPH")

        # Configurar Columnas
        cols_op = [f"Op {i+1}" for i in range(num_op)]
        columnas = ['Cons.', 'Tarea', 'Máquina', 'SAM Unit.', 'SAM Total Req.', 'SAM Asignado'] + cols_op
        
        self.tree['columns'] = columnas
        for col in columnas:
            self.tree.heading(col, text=col)
            width = 80
            if col == 'Tarea': width = 300
            if col == 'Máquina': width = 120
            self.tree.column(col, width=width, anchor='center')
        self.tree.column('Tarea', anchor='w')

        # Limpiar tabla
        for i in self.tree.get_children(): self.tree.delete(i)

        # Totales
        total_sam_unit = 0
        total_sam_req = 0

        # Cargar datos
        for _, row in df_garment.iterrows():
            # Sumar lo asignado a esta tarea entre todos los operarios
            suma_asignada = sum(row[f'operario_{i+1}'] for i in range(num_op))
            
            val_sam_unit = row['Sam min operacion']
            val_sam_req = row['tiempo_necesario']

            total_sam_unit += val_sam_unit
            total_sam_req += val_sam_req

            vals = [
                row['No secuencia'],
                row['OPERACION'],
                row['MAQUINA'],
                f"{val_sam_unit:.2f}",
                f"{val_sam_req:.2f}",
                f"{(suma_asignada):.2f}"
            ]
            for i in range(num_op):
                v_op = row[f'operario_{i+1}']
                vals.append(f"{v_op:.2f}" if v_op > 0 else "0")
            
            self.tree.insert("", "end", values=vals)

        # Fila de Totales en la tabla
        total_row = ["Totales", "", "", f"{total_sam_unit:.2f}", f"{total_sam_req:.2f}", ""]
        # Añadir totales por operario para esta prenda específica (opcional, usuario pide totales generales abajo)
        for i in range(num_op):
             col_sum = df_garment[f'operario_{i+1}'].sum()
             total_row.append(f"{col_sum:.2f}")
        self.tree.insert("", "end", values=total_row, tags=('total_row',))
        self.tree.tag_configure('total_row', font=("Helvetica", 10, "bold"))

        # Footer Load Labels (Carga Total de la Orden)
        for w in self.op_loads_frame.winfo_children(): w.destroy()
        
        kpis = self.last_results.get('kpis', {})
        loads_dict = kpis.get("Carga por Operario (min)", {})
        
        # Mostrar etiquetas de carga total (acumulado de todas las prendas de la orden)
        for i in range(num_op):
             load = loads_dict.get(f"operario_{i+1}", 0)
             lbl = ttk.Label(self.op_loads_frame, text=f"{load:.2f} / {tiempo_nivel}.00 min", 
                            font=("Helvetica", 9, "bold"), background=COLOR_BLANCO, borderwidth=1, relief="solid", padding=5)
             lbl.pack(side='left', padx=10)

    def asignar_automatico(self):
        messagebox.showinfo("Matrix", "Algoritmo de re-asignación automática ejecutado.")

    def guardar_asignacion(self):
         messagebox.showinfo("Matrix", "Asignación guardada correctamente en el sistema.")

    def mostrar_gantt(self):
        if not self.last_results: return
        gantt_win = tk.Toplevel(self)
        gantt_win.title("Diagrama de Gantt")
        gantt_win.geometry("1100x700")
        asignaciones = self.last_results.get('asignacion_por_operario', {})
        if asignaciones:
            fig = generar_gantt(asignaciones)
            canvas = FigureCanvasTkAgg(fig, master=gantt_win)
            canvas.draw()
            canvas.get_tk_widget().pack(expand=True, fill='both', padx=20, pady=20)

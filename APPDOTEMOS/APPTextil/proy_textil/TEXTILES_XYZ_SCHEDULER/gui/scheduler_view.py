# gui/scheduler_view.py (v5.3)
# Módulo para configuración, selección de órdenes y ejecución de balanceo.
# NOVEDAD v5.3: UI modernizada según el diseño de "Nivelación de Carga de Trabajo".

import tkinter as tk
from tkinter import ttk, messagebox
from src.data_loader import data_loader
from src.scheduling_engine import calcular_datos_iniciales, balanceo_heuristico_secuencial
from src.gantt_utils import generar_gantt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui.theme import FONT_TITULO, FONT_SUBTITULO, FONT_NORMAL, COLOR_BLANCO

class SchedulerView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        print("SchedulerView cargado") # Paso 2 de diagnóstico

        # --- Estilos Locales ---
        style = ttk.Style()
        style.configure("Card.TFrame", background=COLOR_BLANCO)

        # --- Variables ---
        self.num_operarios_var = tk.IntVar(value=5)
        self.tiempo_operario_var = tk.IntVar(value=480)
        self.unidad_nivelacion_var = tk.IntVar(value=60)
        self.tamano_paquete_var = tk.IntVar(value=10)
        self.ordenes_seleccionadas = []

        # --- Título y Navegación ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', padx=20, pady=(10, 0))

        btn_home = ttk.Button(top_frame, text="< Volver",
                              command=lambda: controller.show_frame("LandingPage"))
        btn_home.pack(side='left')

        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=20, pady=10)

        title_label = ttk.Label(header_frame, text="Nivelación de Carga de Trabajo", font=FONT_TITULO)
        title_label.pack(anchor='w')
        
        subtitle_label = ttk.Label(header_frame, text="Configure operarios, seleccione órdenes y prepárese para la asignación de tareas.", font=FONT_NORMAL)
        subtitle_label.pack(anchor='w')

        # --- Fila de Parámetros Superiores ---
        params_row = ttk.Frame(self)
        params_row.pack(fill='x', padx=20, pady=10)

        # 1. Configuración
        config_frame = ttk.LabelFrame(params_row, text="Configuración", padding=10)
        config_frame.pack(side='left', fill='y', padx=(0, 10))

        ttk.Label(config_frame, text="# Operarios:").pack(anchor='w')
        ttk.Entry(config_frame, textvariable=self.num_operarios_var, width=25).pack(pady=(0, 10))

        ttk.Label(config_frame, text="Tiempo por Turno (min):").pack(anchor='w')
        ttk.Entry(config_frame, textvariable=self.tiempo_operario_var, width=25).pack()

        # Ocultar la sección vieja de lote y paquete
        self.tamano_paquete_var.set(0)

        # 3. Estadísticas Iniciales
        stats_frame = ttk.LabelFrame(params_row, text="Estadísticas Iniciales", padding=10)
        stats_frame.pack(side='left', expand=True, fill='both', padx=(10, 0))
        self.lbl_stats = ttk.Label(stats_frame, text="Seleccione una orden para ver las estadísticas.", font=FONT_NORMAL)
        self.lbl_stats.pack(expand=True)

        # --- Cuerpo Principal (Selección y Resumen) ---
        body_frame = ttk.Frame(self)
        body_frame.pack(expand=True, fill='both', padx=20, pady=10)

        # Lado Izquierdo: 1. Seleccionar Órdenes
        select_frame = ttk.LabelFrame(body_frame, text="1. Seleccionar Órdenes a Producir", padding=10)
        select_frame.pack(side='left', expand=True, fill='both', padx=(0, 5))

        # ÁREA DE TABLA (PUESTA DESPUÉS DEL BOTÓN PARA QUE EL BOTÓN TENGA PRIORIDAD AL EXPANDIR)
        btn_refresh = ttk.Button(select_frame, text="Refrescar Lista", command=self.actualizar_lista_ordenes)
        btn_refresh.pack(side='bottom', fill='x', pady=5)

        self.tree_op = ttk.Treeview(select_frame, columns=('ID Orden', 'Cliente', 'Fecha Entrega'), show='headings', height=8)
        self.tree_op.heading('ID Orden', text='ID Orden')
        self.tree_op.heading('Cliente', text='Cliente')
        self.tree_op.heading('Fecha Entrega', text='Fecha Entrega')
        self.tree_op.pack(side='top', expand=True, fill='both')
        self.tree_op.bind("<<TreeviewSelect>>", self.al_seleccionar_la_orden)

        # Lado Derecho: 2. Carga de Trabajo
        workload_frame = ttk.LabelFrame(body_frame, text="2. Carga de Trabajo Requerida", padding=10)
        workload_frame.pack(side='left', expand=True, fill='both', padx=(5, 0))

        # ÁREA DE TABLA (BOTÓN ABAJO)
        self.btn_nivelar = ttk.Button(workload_frame, text="Nivelar Trabajos →", command=self.ejecutar_balanceo, state='disabled')
        self.btn_nivelar.pack(side='bottom', fill='x', pady=5)

        self.tree_workload = ttk.Treeview(workload_frame, columns=('Operacion', 'Operarios', 'Carga', 'SAM'), show='headings', height=8)
        self.tree_workload.heading('Operacion', text='Operacion')
        self.tree_workload.heading('Operarios', text='Operarios')
        self.tree_workload.heading('Carga', text='Carga')
        self.tree_workload.heading('SAM', text='SAM')
        self.tree_workload.column('Carga', width=80, anchor='center')
        self.tree_workload.column('Operarios', width=80, anchor='center')
        self.tree_workload.pack(side='top', expand=True, fill='both')

        self.actualizar_lista_ordenes()

    def actualizar_lista_ordenes(self):
        for i in self.tree_op.get_children(): self.tree_op.delete(i)
        # Limpiar stats y tabla de carga también al refrescar total
        for i in self.tree_workload.get_children(): self.tree_workload.delete(i)
        for widget in self.lbl_stats.winfo_children(): widget.destroy()
        self.btn_nivelar.config(state='disabled')
        
        df_log = data_loader.obtener_orders_log()
        if not df_log.empty:
            for _, row in df_log.iterrows():
                cliente = row.get('CLIENTE') or 'N/A'
                fecha = row.get('FECHA_ENTREGA') or 'N/A'
                # Simular checkbox usando el ID
                self.tree_op.insert("", "end", values=(row['OP_UNIQUE_ID'], cliente, fecha))

    def al_seleccionar_la_orden(self, event):
        item_id = self.tree_op.focus()
        if not item_id: return
        
        selected_vals = self.tree_op.item(item_id, 'values')
        op_id = selected_vals[0]
        
        # 1. Obtener detalles básicos de la orden
        detalle_df = data_loader.obtener_detalle_orden(op_id)
        
        # Limpiar tabla de carga y área de stats
        for i in self.tree_workload.get_children(): self.tree_workload.delete(i)
        for widget in self.lbl_stats.winfo_children(): widget.destroy()
        
        if detalle_df is None or detalle_df.empty:
            ttk.Label(self.lbl_stats, text="No se encontraron detalles para esta orden.", foreground="orange").pack()
            self.btn_nivelar.config(state='disabled')
            return

        # 2. MOSTRAR INMEDIATAMENTE (Paso 1 del requerimiento)
        # Cargamos las referencias y cantidades en la tabla de la derecha.
        for _, row in detalle_df.iterrows():
            ref = str(row.get('REFERENCIA', 'N/A'))
            cant = str(row.get('CANTIDAD', '0'))
            self.tree_workload.insert("", "end", values=(f"Ref: {ref}", f"{cant} unds"))
        
        # 3. Intentar cálculos de BOM (Paso 2)
        try:
            num_op = self.num_operarios_var.get()
            
            # Calculamos las estadísticas basándonos 100% en las cantidades de la orden
            datos_calc = calcular_datos_iniciales(detalle_df, num_op)
            
            if "error" in datos_calc:
                # Mostrar el error de BOM pero dejar la lista visible (Punto 4)
                err_msg = str(datos_calc["error"])
                ttk.Label(self.lbl_stats, text=err_msg, foreground="red", wraplength=400, justify="left", font=("Helvetica", 10, "bold")).pack(padx=10, pady=10)
                self.btn_nivelar.config(state='disabled')
                return

            # Si el BOM existe, MEJORAR LA CARGA DE TRABAJO REQUERIDA (Punto 5)
            # Limpiamos el resumen previo (Ref: Qty) para poner las operaciones reales
            for i in self.tree_workload.get_children(): self.tree_workload.delete(i)
            
            df_inicial = datos_calc["tabla_datos_iniciales"]
            for _, row_op in df_inicial.iterrows():
                # Encontrar la cantidad de la orden para este producto
                ref_target = str(row_op['codigo_producto'])
                match_cant = detalle_df[detalle_df['REFERENCIA'].astype(str) == ref_target]
                cant_lote = float(match_cant.iloc[0]['CANTIDAD']) if not match_cant.empty else 0
                
                sam_total_op = float(row_op['Sam min operacion']) * cant_lote
                desc_op = str(row_op['OPERACION'])
                self.tree_workload.insert("", "end", values=(desc_op, "1", "100%", f"{sam_total_op:.2f}"))

            # 4. Mostrar Estadísticas Iniciales (Punto 3 y 8)
            canvas_stats = tk.Canvas(self.lbl_stats, bg=COLOR_BLANCO, highlightthickness=0)
            scrollbar_stats = ttk.Scrollbar(self.lbl_stats, orient="vertical", command=canvas_stats.yview)
            scrollable_frame = ttk.Frame(canvas_stats, style="Card.TFrame")
            
            scrollable_frame.bind("<Configure>", lambda e: canvas_stats.configure(scrollregion=canvas_stats.bbox("all")))
            canvas_stats.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas_stats.configure(yscrollcommand=scrollbar_stats.set)
            
            canvas_stats.pack(side="left", fill="both", expand=True)
            scrollbar_stats.pack(side="right", fill="y")

            for item_stat in datos_calc["indicadores_produccion"]:
                f_item = ttk.Frame(scrollable_frame, style="Card.TFrame", padding=10)
                f_item.pack(fill='x', pady=5)
                
                # Validación estricta de tipos previo al display (Punto 3)
                txt_nombre = str(item_stat.get('Nombre', 'N/A'))
                txt_lote = str(item_stat.get('Cantidad', '0'))
                txt_sam = str(item_stat.get('SAM Total Producto', '0'))
                
                # Extraemos y convertimos el valor como float limpio
                raw_req = item_stat.get('Tiempo Total Requerido', '0 min').replace(' min', '')
                t_req = float(raw_req)
                
                # Lógica del Usuario
                t_turno = float(self.tiempo_operario_var.get())
                t_disp_total = t_turno * num_op
                diferencia = t_disp_total - t_req

                ttk.Label(f_item, text=txt_nombre, font=("Helvetica", 12, "bold"), background=COLOR_BLANCO).pack(anchor='w')
                
                detalles = [
                    f"Tamaño de lote: {txt_lote} un",
                    f"Trabajo Total Requerido: {t_req:.2f} minutos",
                    f"Capacidad de Hoy: {t_disp_total:.2f} minutos disponibles"
                ]
                for d in detalles:
                    ttk.Label(f_item, text=str(d), font=("Helvetica", 10), background=COLOR_BLANCO).pack(anchor='w', padx=15)

                # Mensaje dinámico tipo semáforo
                if diferencia >= 0:
                    msg = f"🟢 Esta orden se puede terminar HOY en el mismo turno y te sobrarán {diferencia:.2f} minutos libres."
                    color_lbl = "darkgreen"
                else:
                    msg = f"🔴 FALTAN {abs(diferencia):.2f} minutos. No vas a alcanzar a sacar esta orden hoy con estos operarios y turno."
                    color_lbl = "red"
                
                ttk.Label(f_item, text=msg, font=("Helvetica", 10, "bold"), foreground=color_lbl, background=COLOR_BLANCO).pack(anchor='w', pady=5)

            self.btn_nivelar.config(state='normal')
            
        except Exception as e:
            # Manejo robusto (Punto 4 y 9)
            err_lbl = ttk.Label(self.lbl_stats, text=f"Error en cálculo de estadísticas:\n{str(e)}", foreground="red")
            err_lbl.pack(padx=20, pady=20)
            print(f"DEBUG Error Stats: {e}")
            self.btn_nivelar.config(state='disabled')

    def ejecutar_balanceo(self):
        item_id = self.tree_op.focus()
        if not item_id: 
            messagebox.showwarning("Scheduler", "Debe seleccionar una orden primero")
            return
        
        # Recuperar parámetros (Corregido)
        op_id = self.tree_op.item(item_id, 'values')[0]
        num_op = self.num_operarios_var.get()
        tam_paq = self.tamano_paquete_var.get()
        
        detalle_orden_df = data_loader.obtener_detalle_orden(op_id)
        if detalle_orden_df is None or detalle_orden_df.empty:
            messagebox.showwarning("Scheduler", "No hay operaciones para balancear")
            return

        try:
            # 1. Calcular Datos Iniciales con base al 100% de la orden
            df_datos_iniciales = calcular_datos_iniciales(detalle_orden_df, num_op)
            if "error" in df_datos_iniciales:
                messagebox.showerror("Scheduler", f"Error en el BOM: {df_datos_iniciales['error']}")
                return

            # Tiempo límite literal por operario
            df_tabla = df_datos_iniciales["tabla_datos_iniciales"]
            tiempo_turno = float(self.tiempo_operario_var.get())
            
            if num_op <= 0:
                messagebox.showerror("Error", "El número de operarios debe ser mayor a 0")
                return

            # Ejecutar Algoritmo llenando a los operarios hasta donde el turno se los permita
            resultado = balanceo_heuristico_secuencial(
                df_tabla, 
                num_op, 
                tiempo_turno
            )
            
            if "error" in resultado:
                messagebox.showerror("Scheduler", f"Error ejecutando balanceo: {resultado['error']}")
                return

            # 3. Navegar a la vista de resultados
            params = {
                "num_operarios": num_op,
                "tamano_paquete": 0,
                "tiempo_nivel": round(tiempo_turno, 2)
            }
            
            # Incluir indicadores para mostrar UPH en la matriz
            resultado["indicadores_produccion"] = df_datos_iniciales.get("indicadores_produccion", [])
            
            # Guardar en el controlador para que Reportes pueda leerlo (Punto 1 y 9)
            if self.controller.programming_results is None:
                self.controller.programming_results = {}
            
            resultado["op_id"] = op_id
            resultado["params"] = params
            self.controller.programming_results[op_id] = resultado
            
            # Punto 7 y 8: Navegación via controller
            self.controller.show_assignment_view(resultado, params)

            # Guardar "historial" para operarios, maquinas y procesos
            import json
            actividades = []
            df_res = resultado["df_resultado"]
            for _, r in df_res.iterrows():
                proc = r.get('PROCESO', 'ENSAMBLE')
                maq = r.get('MAQUINA', 'Manual')
                cons = r.get('No secuencia', 0)
                for i in range(num_op):
                    t_asig = r.get(f'operario_{i+1}', 0)
                    if t_asig > 0:
                        actividades.append([
                            f"Operario {i+1}",
                            int(cons),
                            str(proc),
                            str(maq),
                            float(t_asig)
                        ])
            
            resultado_historial = json.dumps({"actividades": actividades})
            data_loader.guardar_historial_schedule(op_id, json.dumps(params), resultado_historial)

            # Marcar como balanceada
            data_loader.actualizar_estado_orden(op_id, "Balanceada")
            
        except Exception as e:
            messagebox.showerror("Scheduler", f"Error crítico: {e}")

    def mostrar_resultados(self, resultado):
        res_win = tk.Toplevel(self)
        res_win.title("Matriz de Asignación")
        res_win.geometry("1300x800")
        res_win.configure(bg=COLOR_BLANCO)

        if resultado.get("error"):
            ttk.Label(res_win, text=f"Error: {resultado['error']}", foreground="red", font=FONT_SUBTITULO).pack(pady=50)
            return

        # --- Cabecera de la Matriz ---
        header_frame = ttk.Frame(res_win, padding=20, style="Dashboard.TFrame")
        header_frame.pack(fill='x')
        
        ttk.Label(header_frame, text="Matriz de Asignación", font=FONT_TITULO, background=COLOR_BLANCO).pack(anchor='w')
        
        # Obtener nombres de prendas
        df_res = resultado['df_resultado']
        prendas = ", ".join(df_res['nombre_producto'].unique()) if 'nombre_producto' in df_res.columns else "N/A"
        ttk.Label(header_frame, text=f"Prenda(s): {prendas}", font=FONT_SUBTITULO, background=COLOR_BLANCO).pack(anchor='w', pady=5)

        # Parámetros adicionales
        num_op = self.num_operarios_var.get()
        tam_paq = self.tamano_paquete_var.get()
        tiempo_nivel = self.tiempo_operario_var.get()
        
        params_text = f"Tamaño de paquete: {tam_paq} | Tiempo de Nivelación: {tiempo_nivel} min | Operarios: {num_op}"
        ttk.Label(header_frame, text=params_text, font=FONT_NORMAL, background=COLOR_BLANCO).pack(anchor='w')

        # --- Tabla de la Matriz ---
        # Columnas dinámicas de operarios
        cols_op = [f"Op {i+1}" for i in range(num_op)]
        columnas = ['Cons.', 'Tarea', 'Máquina', 'SAM Unit.', 'T. Paquete', 'SAM Total Req.', 'SAM Asignado'] + cols_op
        
        table_frame = ttk.Frame(res_win, padding=10)
        table_frame.pack(expand=True, fill='both')

        tree_matriz = ttk.Treeview(table_frame, columns=columnas, show='headings', height=20)
        
        for col in columnas:
            tree_matriz.heading(col, text=col)
            width = 80
            if col == 'Tarea': width = 250
            if col == 'Máquina': width = 120
            tree_matriz.column(col, width=width, anchor='center')

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree_matriz.yview)
        tree_matriz.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        tree_matriz.pack(expand=True, fill='both')

        # Insertar datos
        for _, row in df_res.iterrows():
            suma_asignada = sum(row[f'operario_{i+1}'] for i in range(num_op))
            
            vals = [
                row['No secuencia'],
                f"{row['OPERACION']} ({row['codigo_producto']})",
                row['MAQUINA'],
                f"{row['Sam min operacion']:.2f}",
                f"{row['Sam min operacion'] * tam_paq:.2f}",
                f"{row['tiempo_necesario']:.2f}",
                f"{suma_asignada:.2f}"
            ]
            for i in range(num_op):
                val_op = row[f'operario_{i+1}']
                vals.append(f"{val_op:.2f}" if val_op > 0 else "0")
            
            tree_matriz.insert("", "end", values=vals)

        # --- Footer ---
        footer_frame = ttk.Frame(res_win, padding=20)
        footer_frame.pack(fill='x')

        kpi_text = " | ".join([f"{k}: {v}" for k, v in resultado.get('kpis', {}).items() if "Global" in k or "%" in k])
        ttk.Label(footer_frame, text=kpi_text, font=FONT_NORMAL).pack(side='left')

        def ver_gantt():
            gantt_win = tk.Toplevel(res_win)
            gantt_win.title("Diagrama de Gantt")
            asignaciones = resultado.get('asignacion_por_operario', {})
            if asignaciones:
                fig = generar_gantt(asignaciones)
                canvas = FigureCanvasTkAgg(fig, master=gantt_win)
                canvas.draw()
                canvas.get_tk_widget().pack(expand=True, fill='both', padx=20, pady=20)

        ttk.Button(footer_frame, text="Ver Diagrama de Gantt", command=ver_gantt).pack(side='right', padx=10)
        ttk.Button(footer_frame, text="Cerrar", command=res_win.destroy).pack(side='right', padx=10)

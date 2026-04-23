import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
from pathlib import Path
import os
import shutil
import webbrowser

from gui.theme import (FONT_TITULO, FONT_SUBTITULO, FONT_NORMAL, FONT_MENU, 
                       COLOR_FONDO_CLARO, COLOR_BLANCO, COLOR_NEGRO, 
                       COLOR_PRIMARIO, COLOR_TARJETA)
from src.data_loader import data_loader
from src.scheduling_engine import calcular_datos_iniciales, balanceo_heuristico_secuencial
from src.report_generator import PDFReport

class ReportsView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(style="Dashboard.TFrame")
        
        # Estado Interno
        self.current_orders = []
        self.assigned_orders = []
        self.pending_orders = []
        self.actividades_operarios = []
        self.kpis = {}

        self.crear_interfaz()
        
    def crear_interfaz(self):
        style = ttk.Style()
        style.configure("Dashboard.TFrame", background=COLOR_FONDO_CLARO)

        # --- MAIN CANVAS FOR SCROLLING ---
        self.main_canvas = tk.Canvas(self, bg=COLOR_FONDO_CLARO, highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas, style="Dashboard.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )

        self.canvas_frame_id = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        self.main_canvas.bind('<Configure>', lambda e: self.main_canvas.itemconfig(self.canvas_frame_id, width=e.width))

        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_scrollbar.pack(side="right", fill="y")
        
        # --- HEADER PRINCIPAL ---
        header = tk.Frame(self.scrollable_frame, bg=COLOR_FONDO_CLARO, pady=15, padx=20)
        header.pack(fill='x')
        
        # Título
        tk.Label(header, text="Reportes y Analíticas", font=("Helvetica", 24, "bold"), fg=COLOR_PRIMARIO, bg=COLOR_FONDO_CLARO).pack(side='left', anchor='n')

        # Botones Superiores (Izquierda)
        top_btns = tk.Frame(header, bg=COLOR_FONDO_CLARO)
        top_btns.pack(side='right', anchor='n')
        
        btn_imprimir = tk.Button(top_btns, text="🖨️ Imprimir Actividades por Operario", font=FONT_MENU, bg=COLOR_BLANCO, fg=COLOR_PRIMARIO, relief="solid", bd=1, padx=10, pady=5, command=self.abrir_ventana_operarios)
        btn_imprimir.pack(side='left', padx=5)
        
        btn_reporte = tk.Button(top_btns, text="📄 Reporte para Gerente General", font=FONT_MENU, bg=COLOR_PRIMARIO, fg=COLOR_BLANCO, relief="flat", padx=10, pady=5, command=self.exportar_pdf_gerente)
        btn_reporte.pack(side='left', padx=5)

        # --- BARRA DE FILTROS ---
        filtros = tk.Frame(self.scrollable_frame, bg=COLOR_FONDO_CLARO, padx=20)
        filtros.pack(fill='x', pady=5)
        
        tk.Label(filtros, text="Fecha:", font=FONT_NORMAL, bg=COLOR_FONDO_CLARO).pack(side='left')
        
        self.combo_fecha = ttk.Combobox(filtros, state='normal', width=12, font=FONT_NORMAL)
        hoy = datetime.now().strftime("%d/%m/%Y")
        self.combo_fecha.set(hoy)
        self.combo_fecha.pack(side='left', padx=10)
        
        tk.Label(filtros, text="Mostrar:", font=FONT_NORMAL, bg=COLOR_FONDO_CLARO).pack(side='left', padx=(15, 5))
        self.combo_mostrar = ttk.Combobox(filtros, values=["Solo fecha seleccionada", "Ver todas las fechas"], state='readonly', width=25, font=FONT_NORMAL)
        self.combo_mostrar.current(0)
        self.combo_mostrar.pack(side='left', padx=5)
        
        btn_actualizar = tk.Button(filtros, text="🔄 Actualizar", bg=COLOR_PRIMARIO, fg=COLOR_BLANCO, font=FONT_MENU, relief='flat', padx=10, command=self.recalcular_y_actualizar)
        btn_actualizar.pack(side='left', padx=15)

        # --- SECCIÓN KPIs ---
        self.kpi_frame = tk.Frame(self.scrollable_frame, bg=COLOR_FONDO_CLARO, padx=15)
        self.kpi_frame.pack(fill='x', pady=15)
        for i in range(5):
            self.kpi_frame.columnconfigure(i, weight=1, uniform='kpi')
            
        self.lbl_kpis = []
        kpi_titles = ["Órdenes Programadas", "Órdenes Asignadas", "Órdenes Pendientes", "Tiempo Total Carga", "Utilización Promedio"]
        kpi_desc = ["Total órdenes", "Según capacidad", "Por capacidad limitada", "Carga del día", "Eficiencia de la línea"]
        
        for i in range(5):
            c = tk.Frame(self.kpi_frame, bg=COLOR_TARJETA, padx=15, pady=15, highlightbackground="#E2E8F0", highlightthickness=1)
            c.grid(row=0, column=i, padx=5, sticky='nsew')
            tk.Label(c, text=kpi_titles[i], font=("Helvetica", 10, "bold"), fg=COLOR_PRIMARIO, bg=COLOR_TARJETA, wraplength=120).pack(anchor='center')
            val_lbl = tk.Label(c, text="0", font=("Helvetica", 20, "bold"), fg=COLOR_PRIMARIO, bg=COLOR_TARJETA)
            val_lbl.pack(pady=5)
            tk.Label(c, text=kpi_desc[i], font=("Helvetica", 9), fg="#64748b", bg=COLOR_TARJETA).pack(anchor='center')
            self.lbl_kpis.append(val_lbl)

        # --- CONTENIDO PRINCIPAL (Split Horizontal) ---
        main_body = tk.Frame(self.scrollable_frame, bg=COLOR_FONDO_CLARO, padx=20)
        main_body.pack(expand=True, fill='both')
        
        # Izquierda (Tablas)
        left_panel = tk.Frame(main_body, bg=COLOR_FONDO_CLARO)
        left_panel.pack(side='left', expand=True, fill='both', pady=5)
        
        # Tabla 1: Órdenes Programadas
        tk.Label(left_panel, text="Órdenes Programadas para el Día", font=("Helvetica", 12, "bold"), bg=COLOR_FONDO_CLARO, fg=COLOR_NEGRO).pack(anchor='w', pady=5)
        
        ord_frame = tk.Frame(left_panel)
        ord_frame.pack(fill='both', expand=True)
        ord_scroll_y = ttk.Scrollbar(ord_frame, orient='vertical')
        ord_scroll_x = ttk.Scrollbar(ord_frame, orient='horizontal')

        cols_ord = ('Orden', 'Cliente', 'Producto', 'Prioridad', 'Fecha Entrega', 'Estado', 'Tiempo Total', 'Tiempo Prog.', 'Asignada')
        self.tree_ordenes = ttk.Treeview(ord_frame, columns=cols_ord, show='headings', height=6, yscrollcommand=ord_scroll_y.set, xscrollcommand=ord_scroll_x.set)
        ord_scroll_y.config(command=self.tree_ordenes.yview)
        ord_scroll_x.config(command=self.tree_ordenes.xview)
        
        ord_scroll_y.pack(side='right', fill='y')
        ord_scroll_x.pack(side='bottom', fill='x')
        for c in cols_ord:
            self.tree_ordenes.heading(c, text=c)
            w = 120 if c in ('Orden', 'Cliente', 'Producto', 'Fecha Entrega') else 90
            self.tree_ordenes.column(c, width=w, anchor='center', stretch=False)
        self.tree_ordenes.pack(fill='both', expand=True)

        self.tree_ordenes.tag_configure("estado_v", foreground="green")
        self.tree_ordenes.tag_configure("estado_x", foreground="red")
        self.tree_ordenes.tag_configure("estado_p", foreground="orange")

        # Tabla 2: Actividades por Operario
        tk.Label(left_panel, text="Plan de Actividades por Operario", font=("Helvetica", 12, "bold"), bg=COLOR_FONDO_CLARO, fg=COLOR_NEGRO).pack(anchor='w', pady=(15, 5))
        
        act_frame = tk.Frame(left_panel)
        act_frame.pack(fill='both', expand=True)
        act_scroll_y = ttk.Scrollbar(act_frame, orient='vertical')
        act_scroll_x = ttk.Scrollbar(act_frame, orient='horizontal')

        cols_act = ('Operario', 'Orden', 'Proceso', 'Máquina', 'Tiempo (min)')
        self.tree_acts = ttk.Treeview(act_frame, columns=cols_act, show='headings', height=6, yscrollcommand=act_scroll_y.set, xscrollcommand=act_scroll_x.set)
        act_scroll_y.config(command=self.tree_acts.yview)
        act_scroll_x.config(command=self.tree_acts.xview)
        
        act_scroll_y.pack(side='right', fill='y')
        act_scroll_x.pack(side='bottom', fill='x')
        for c in cols_act:
            self.tree_acts.heading(c, text=c)
            w = 80 if c == 'Tiempo (min)' else 120
            w = 200 if c == 'Proceso' else w
            self.tree_acts.column(c, width=w, anchor='center', stretch=False)
        self.tree_acts.pack(fill='both', expand=True)
        
        # Derecha (Panel Info)
        right_panel = tk.Frame(main_body, bg=COLOR_FONDO_CLARO, width=300)
        right_panel.pack(side='right', fill='y', padx=(20, 0))
        
        # Resumen Capacidad
        cap_frame = tk.Frame(right_panel, bg=COLOR_TARJETA, padx=15, pady=15, highlightbackground="#E2E8F0", highlightthickness=1)
        cap_frame.pack(fill='x', pady=5)
        tk.Label(cap_frame, text="Capacidad de Operarios (Hoy)", font=("Helvetica", 11, "bold"), bg=COLOR_TARJETA).pack(anchor='w', pady=(0, 10))
        
        self.lbl_cap_ops = tk.Label(cap_frame, text="Operarios Disponibles: 0", font=FONT_NORMAL, bg=COLOR_TARJETA)
        self.lbl_cap_ops.pack(anchor='w', pady=2)
        self.lbl_cap_disp = tk.Label(cap_frame, text="Tiempo Disponible Total: 0.00 min", font=FONT_NORMAL, bg=COLOR_TARJETA)
        self.lbl_cap_disp.pack(anchor='w', pady=2)
        self.lbl_cap_prog = tk.Label(cap_frame, text="Tiempo Programado: 0.00 min", font=FONT_NORMAL, bg=COLOR_TARJETA)
        self.lbl_cap_prog.pack(anchor='w', pady=2)
        self.lbl_cap_util = tk.Label(cap_frame, text="Utilización: 0.0%", font=("Helvetica", 10, "bold"), fg="darkgreen", bg=COLOR_TARJETA)
        self.lbl_cap_util.pack(anchor='w', pady=(5, 0))
        
        # Al arrancar, refrescar
        self.recalcular_y_actualizar()

    def get_operarios_disponibles(self):
        try:
            return self.controller.frames["SchedulerView"].num_operarios_var.get()
        except:
            return 5 # Fallback
            
    def get_minutos_turno(self):
        try:
            return self.controller.frames["SchedulerView"].tiempo_operario_var.get()
        except:
            return 480 # Fallback

    def calcular_tiempo_orden(self, op_id):
        detalle_df = data_loader.obtener_detalle_orden(op_id)
        if detalle_df is None or detalle_df.empty: return 0, 'N/A'
        
        producto = "Varios"
        if 'REFERENCIA' in detalle_df.columns:
            producto = ", ".join(detalle_df['REFERENCIA'].astype(str).unique())
            
        datos = calcular_datos_iniciales(detalle_df, 1)
        if "error" in datos: return 0, producto
        
        total = 0
        for ind in datos.get("indicadores_produccion", []):
            try:
                raw = str(ind.get('Tiempo Total Requerido', '0')).replace(' min', '')
                total += float(raw)
            except: pass
        return total, producto

    def recalcular_y_actualizar(self):
        # 1. Obtener órdenes y parámetros
        df_ord = data_loader.obtener_orders_log()
        num_op = self.get_operarios_disponibles()
        min_turno = self.get_minutos_turno()
        cap_total = num_op * min_turno
        
        if df_ord.empty:
            return

        # Actualizar lista de fechas en el combobox
        fechas_existentes = sorted(df_ord['FECHA_ENTREGA'].dropna().unique().tolist())
        fecha_actual = self.combo_fecha.get()
        if fecha_actual not in fechas_existentes and fecha_actual != "":
            fechas_existentes.append(fecha_actual)
            fechas_existentes.sort()
        self.combo_fecha['values'] = fechas_existentes

        # Filtrar por fecha si es necesario
        if self.combo_mostrar.get() == "Solo fecha seleccionada":
            fecha_filtro = self.combo_fecha.get()
            if fecha_filtro:
                df_ord = df_ord[df_ord['FECHA_ENTREGA'] == fecha_filtro]
            
        # 2. Re-calcular capacidades y asignaciones
        ords_enrich = []
        for _, row in df_ord.iterrows():
            op_id = row['OP_UNIQUE_ID']
            tiempo_req, prod_name = self.calcular_tiempo_orden(op_id)
            ords_enrich.append({
                'id': op_id,
                'cliente': row.get('CLIENTE', 'N/A'),
                'producto': prod_name,
                'prioridad': int(row.get('PRIORIDAD', 5)),
                'fecha_ent': row.get('FECHA_ENTREGA', 'N/A'),
                'tiempo_req': float(tiempo_req),
                'tiempo_prog': 0.0,
                'estado': 'Pendiente',
                'asignada': False
            })
            
        # Ordenar por prioridad (1 = Urgente)
        ords_enrich.sort(key=lambda x: (x['prioridad'], x['tiempo_req']))
        
        tiempo_restante = cap_total
        tiempo_programado_total = 0
        ordenes_asignadas = 0
        ordenes_parciales = 0
        
        # Asignar basado en capacidad
        for o in ords_enrich:
            if o['tiempo_req'] <= 0:
                continue
            if tiempo_restante >= o['tiempo_req']:
                # Asignación completa
                o['estado'] = 'Asignada'
                o['asignada'] = True
                o['tiempo_prog'] = o['tiempo_req']
                tiempo_restante -= o['tiempo_req']
                tiempo_programado_total += o['tiempo_req']
                ordenes_asignadas += 1
            elif tiempo_restante > 0:
                # Asignación parcial - Fraccionamiento de lote
                o['estado'] = 'Parcialmente Asignada'
                o['asignada'] = False # Partial
                o['tiempo_prog'] = tiempo_restante
                tiempo_programado_total += tiempo_restante
                tiempo_restante = 0
                ordenes_parciales += 1
            else:
                o['estado'] = 'Pendiente'
        
        self.current_orders = ords_enrich
        
        # 3. Renderizar KPIs
        self.lbl_kpis[0].config(text=f"{len(ords_enrich)}")
        self.lbl_kpis[1].config(text=f"{ordenes_asignadas + ordenes_parciales}")
        self.lbl_kpis[2].config(text=f"{len(ords_enrich) - ordenes_asignadas - ordenes_parciales}")
        self.lbl_kpis[3].config(text=f"{tiempo_programado_total:.2f} min")
        
        utilizacion = (tiempo_programado_total / cap_total * 100) if cap_total > 0 else 0
        self.lbl_kpis[4].config(text=f"{utilizacion:.1f}%")
        
        self.lbl_cap_ops.config(text=f"Operarios Disponibles: {num_op}")
        self.lbl_cap_disp.config(text=f"Tiempo Disponible Total: {cap_total:.2f} min")
        self.lbl_cap_prog.config(text=f"Tiempo Programado: {tiempo_programado_total:.2f} min")
        self.lbl_cap_util.config(text=f"Utilización: {utilizacion:.1f}%")

        # 4. Refrescar Tabla Órdenes
        for i in self.tree_ordenes.get_children(): self.tree_ordenes.delete(i)
        
        for o in ords_enrich:
            marca = "✔" if o['estado'] == 'Asignada' else ("⚠" if o['estado'] == 'Parcialmente Asignada' else "✖")
            tag = "estado_v" if o['estado'] == 'Asignada' else ("estado_p" if o['estado'] == 'Parcialmente Asignada' else "estado_x")
            prioridad_visual = str(o['prioridad'])
            self.tree_ordenes.insert("", "end", values=(o['id'], o['cliente'], o['producto'][:15], prioridad_visual, o['fecha_ent'], o['estado'], f"{o['tiempo_req']:.2f}", f"{o['tiempo_prog']:.2f}", marca), tags=(tag,))

        # 5. Generar Plan de Actividades Simulado (Balanceo rápido en memoria)
        for i in self.tree_acts.get_children(): self.tree_acts.delete(i)
        
        ops_actuales = [f"Operario {i+1}" for i in range(num_op)]
        carga_actual_ops = {op: 0 for op in ops_actuales}
        
        self.actividades_operarios = []
        for o in ords_enrich:
            if o['tiempo_prog'] <= 0: continue
            
            detalle = data_loader.obtener_detalle_orden(o['id'])
            if detalle is None or detalle.empty: continue
            
            datos = calcular_datos_iniciales(detalle, num_op)
            if "error" in datos: continue
            
            df_ops = datos['tabla_datos_iniciales']
            
            # Si es parcial, ajustamos todas las sumas por un factor
            factor_parcial = o['tiempo_prog'] / o['tiempo_req'] if o['tiempo_req'] > 0 else 1
            
            for _, op_row in df_ops.iterrows():
                sam_uni = float(op_row['Sam min operacion'])
                ref = op_row['codigo_producto']
                match_cant = detalle[detalle['REFERENCIA'].astype(str) == str(ref)]
                cant_lote = float(match_cant.iloc[0]['CANTIDAD']) if not match_cant.empty else 0
                
                tiempo_op = sam_uni * cant_lote * factor_parcial
                if tiempo_op <= 0: continue
                
                # Asignar al operario con menos carga
                op_elegido = min(carga_actual_ops, key=carga_actual_ops.get)
                carga_actual_ops[op_elegido] += tiempo_op
                
                actividad = (op_elegido, o['id'], op_row['OPERACION'][:20], op_row['MAQUINA'], f"{tiempo_op:.2f}")
                self.tree_acts.insert("", "end", values=actividad)
                self.actividades_operarios.append(actividad)

    def exportar_excel(self):
        try:
            path_descargas = Path.home() / "Downloads"
            ruta = path_descargas / f"reporte_produccion_diaria_{datetime.now().strftime('%Y%m%d')}.csv"
            
            # Crear CSV del plan
            df = pd.DataFrame(self.current_orders)
            df.to_csv(ruta, index=False, sep=';', encoding='utf-8')
            messagebox.showinfo("Exportar", f"Reporte descargado exitosamente en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Exportar", f"Error exportando reporte: {e}")
            
    def exportar_pdf_gerente(self):
        try:
            # Recopilar la información de los KPIs
            kpi_titles = ["Órdenes Programadas", "Órdenes Asignadas", "Órdenes Pendientes", "Tiempo Total Carga", "Utilización Promedio"]
            kpi_values = [lbl.cget("text") for lbl in self.lbl_kpis]
            kpis_html = "".join([f"<div class='kpi-box'><h3>{title}</h3><p>{value}</p></div>" for title, value in zip(kpi_titles, kpi_values)])
            
            # Recopilar información de Órdenes Programadas
            ordenes_html = "<tr><th>Orden</th><th>Cliente</th><th>Producto</th><th>Prioridad</th><th>Fecha Entrega</th><th>Estado</th><th>Tiempo Req (min)</th><th>Tiempo Prog (min)</th></tr>"
            for o in self.current_orders:
                ordenes_html += f"<tr><td>{o['id']}</td><td>{o['cliente']}</td><td>{o['producto']}</td><td>{o['prioridad']}</td><td>{o['fecha_ent']}</td><td>{o['estado']}</td><td>{o['tiempo_req']:.2f}</td><td>{o['tiempo_prog']:.2f}</td></tr>"

            # Recopilar información de Resumen de Operarios (Para el gerente)
            resumen_ops_html = "<tr><th>Operario</th><th>T. Asignado (min)</th><th>Órdenes Principales</th><th>Máquinas</th></tr>"
            
            num_op_g = self.get_operarios_disponibles()
            ops_g = [f"Operario {i+1}" for i in range(num_op_g)]
            
            for op in ops_g:
                acts_op = [act for act in self.actividades_operarios if act[0] == op]
                if not acts_op:
                    resumen_ops_html += f"<tr><td><strong>{op}</strong></td><td>0.00</td><td style='color:#94a3b8;'>Sin carga</td><td style='color:#94a3b8;'>-</td></tr>"
                else:
                    tiempo_op = sum(float(a[4]) for a in acts_op)
                    ordenes_un = list(dict.fromkeys([str(a[1]) for a in acts_op]))
                    maquinas_un = list(dict.fromkeys([str(a[3]) for a in acts_op]))
                    
                    ods_str = ", ".join(ordenes_un[:3]) + ("..." if len(ordenes_un)>3 else "")
                    maqs_str = ", ".join(maquinas_un[:3]) + ("..." if len(maquinas_un)>3 else "")
                    
                    resumen_ops_html += f"<tr><td><strong>{op}</strong></td><td style='color:#2563eb; font-weight:bold;'>{tiempo_op:.2f}</td><td>{ods_str}</td><td>{maqs_str}</td></tr>"

            # Generar el HTML
            html_content = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Reporte Gerencial</title>
                <style>
                    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #334155; margin: 0; padding: 20px; }}
                    .container {{ max-width: 1000px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
                    .header {{ text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; }}
                    h1 {{ color: #0f172a; margin: 0 0 10px 0; font-size: 28px; }}
                    .fecha {{ color: #64748b; font-size: 14px; margin: 0; }}
                    .kpi-container {{ display: flex; justify-content: space-between; margin-bottom: 40px; flex-wrap: wrap; gap: 15px; }}
                    .kpi-box {{ background-color: #f1f5f9; border-radius: 10px; padding: 20px; text-align: center; flex: 1; min-width: 150px; border: 1px solid #e2e8f0; }}
                    .kpi-box h3 {{ font-size: 12px; color: #64748b; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 0.5px; }}
                    .kpi-box p {{ font-size: 24px; font-weight: bold; color: #2563eb; margin: 0; }}
                    h2 {{ color: #1e293b; font-size: 20px; margin-bottom: 20px; border-left: 4px solid #2563eb; padding-left: 10px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; border-radius: 8px; overflow: hidden; }}
                    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 14px 16px; text-align: left; font-size: 14px; }}
                    th {{ background-color: #f8fafc; color: #475569; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }}
                    tr:hover {{ background-color: #f1f5f9; }}
                    .btn-print {{ display: block; width: fit-content; margin: 0 auto 30px auto; padding: 12px 30px; background-color: #2563eb; color: white; text-align: center; text-decoration: none; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; border: none; transition: background-color 0.2s; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2); }}
                    .btn-print:hover {{ background-color: #1d4ed8; }}
                    @media print {{
                        .btn-print {{ display: none; }}
                        body {{ background-color: white; padding: 0; }}
                        .container {{ box-shadow: none; max-width: 100%; padding: 0; margin: 0; border-radius: 0; }}
                        table {{ border: 1px solid #e2e8f0; border-radius: 0; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <button class="btn-print" onclick="window.print()">🖨️ Exportar a PDF / Imprimir</button>
                    
                    <div class="header">
                        <h1>Reporte Gerencial - Estado de Producción</h1>
                        <p class="fecha">Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    </div>
                    
                    <h2>Resumen de Indicadores (KPIs)</h2>
                    <div class="kpi-container">
                        {kpis_html}
                    </div>
                    
                    <h2>Detalle de Órdenes Programadas</h2>
                    <table>
                        {ordenes_html}
                    </table>
                    
                    <h2>Resumen de Carga por Operario</h2>
                    <table>
                        {resumen_ops_html}
                    </table>
                </div>
            </body>
            </html>
            """
            
            # Guardar el archivo HTML
            path_descargas = Path.home() / "Downloads"
            ruta_html = path_descargas / f"reporte_gerencial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(ruta_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            # Abrir en el navegador Default
            webbrowser.open(f'file://{str(ruta_html.resolve())}')
            messagebox.showinfo("Reporte Generado", f"El reporte ha sido generado y abierto en su navegador web.\nDesde ahí puede guardarlo como PDF usando el botón integrado.\n\nUbicación: {ruta_html}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Ha ocurrido un error al generar el reporte: {str(e)}")

    def abrir_ventana_operarios(self):
        # Crear ventana hija
        win = tk.Toplevel(self)
        win.title("Actividades por Operario")
        win.geometry("900x600")
        win.configure(bg=COLOR_FONDO_CLARO)
        
        # Header
        header = tk.Frame(win, bg=COLOR_TARJETA, pady=15, padx=20)
        header.pack(fill='x')
        tk.Label(header, text="Consultar Actividades Individuales", font=("Helvetica", 18, "bold"), fg=COLOR_PRIMARIO, bg=COLOR_TARJETA).pack(side='left')

        # Filtro de Operario
        filtro_frame = tk.Frame(win, bg=COLOR_FONDO_CLARO, pady=15, padx=20)
        filtro_frame.pack(fill='x')
        
        tk.Label(filtro_frame, text="Seleccionar Operario:", font=FONT_NORMAL, bg=COLOR_FONDO_CLARO).pack(side='left', padx=5)
        
        num_op = self.get_operarios_disponibles()
        ops = [f"Operario {i+1}" for i in range(num_op)]
        
        combo_op = ttk.Combobox(filtro_frame, values=ops, state='readonly', width=20, font=FONT_NORMAL)
        if ops: combo_op.current(0)
        combo_op.pack(side='left', padx=10)
        
        # Area de contenido (Tabla)
        table_frame = tk.Frame(win, bg=COLOR_FONDO_CLARO, padx=20, pady=10)
        table_frame.pack(fill='both', expand=True)

        scroll_y = ttk.Scrollbar(table_frame, orient='vertical')
        scroll_x = ttk.Scrollbar(table_frame, orient='horizontal')
        
        cols = ('ID Orden', 'Proceso', 'Máquina', 'Tiempo (min)')
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.config(command=tree.yview)
        scroll_x.config(command=tree.xview)
        scroll_y.pack(side='right', fill='y')
        scroll_x.pack(side='bottom', fill='x')
        
        for c in cols:
            tree.heading(c, text=c)
            width = 150 if c in ('ID Orden', 'Máquina', 'Tiempo (min)') else 300
            tree.column(c, width=width, anchor='center')
        
        tree.pack(fill='both', expand=True)
        
        def actualizar_tabla(*args):
            for i in tree.get_children(): tree.delete(i)
            op_sel = combo_op.get()
            total_tiempo = 0
            for act in self.actividades_operarios:
                if act[0] == op_sel:
                    tree.insert("", "end", values=(act[1], act[2], act[3], act[4]))
                    total_tiempo += float(act[4])
            lbl_total.config(text=f"Tiempo Total Asignado: {total_tiempo:.2f} min / {self.get_minutos_turno():.2f} min max")
            
        combo_op.bind("<<ComboboxSelected>>", actualizar_tabla)
        
        # Footer con el total del tiempo del operario
        footer = tk.Frame(win, bg=COLOR_FONDO_CLARO, pady=10, padx=20)
        footer.pack(fill='x')
        lbl_total = tk.Label(footer, text="Tiempo Total Asignado: 0.00 min", font=("Helvetica", 12, "bold"), fg=COLOR_PRIMARIO, bg=COLOR_FONDO_CLARO)
        lbl_total.pack(side='right')
        
        btn_cerrar = tk.Button(footer, text="Cerrar", font=FONT_NORMAL, bg=COLOR_BLANCO, fg=COLOR_NEGRO, command=win.destroy)
        btn_cerrar.pack(side='left')
        
        btn_imprimir_op = tk.Button(footer, text="🖨️ Imprimir Todos los Operarios", font=FONT_NORMAL, bg=COLOR_PRIMARIO, fg=COLOR_BLANCO, relief="flat", command=self.exportar_pdf_todos_operarios, padx=10)
        btn_imprimir_op.pack(side='left', padx=20)

        # Inicializar
        actualizar_tabla()

    def exportar_pdf_todos_operarios(self):
        try:
            # Obtener lista de operarios
            num_op = self.get_operarios_disponibles()
            ops = [f"Operario {i+1}" for i in range(num_op)]
            
            secciones_html = ""
            
            for op_sel in ops:
                actividades_html = "<tr><th>ID Orden</th><th>Proceso</th><th>Máquina</th><th>Tiempo (min)</th></tr>"
                total_tiempo = 0
                for act in self.actividades_operarios:
                    if act[0] == op_sel:
                        actividades_html += f"<tr><td>{act[1]}</td><td>{act[2]}</td><td>{act[3]}</td><td>{act[4]}</td></tr>"
                        total_tiempo += float(act[4])
                        
                if total_tiempo == 0:
                    actividades_html += "<tr><td colspan='4' style='text-align: center; color: #94a3b8; padding: 20px;'>No hay actividades asignadas para este operario en este día.</td></tr>"
                
                secciones_html += f"""
                <div class="operario-section">
                    <div class="op-header">
                        <h2>{op_sel}</h2>
                        <span class="badge">Total: {total_tiempo:.2f} min</span>
                    </div>
                    <table>
                        {actividades_html}
                    </table>
                </div>
                """

            # Generar el HTML general completo
            html_content = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Reporte de Actividades de Operarios</title>
                <style>
                    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #334155; margin: 0; padding: 20px; }}
                    .container {{ max-width: 1000px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
                    .header {{ text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; }}
                    h1 {{ color: #0f172a; margin: 0 0 10px 0; font-size: 28px; }}
                    .fecha {{ color: #64748b; font-size: 14px; margin: 0; }}
                    .operario-section {{ margin-bottom: 40px; page-break-inside: avoid; }}
                    .op-header {{ display: flex; justify-content: space-between; align-items: center; background-color: #f1f5f9; padding: 15px 20px; border-radius: 8px 8px 0 0; border: 1px solid #e2e8f0; border-bottom: none; }}
                    .op-header h2 {{ color: #1e293b; font-size: 18px; margin: 0; }}
                    .badge {{ background-color: #2563eb; color: white; padding: 6px 12px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
                    table {{ width: 100%; border-collapse: collapse; overflow: hidden; border: 1px solid #e2e8f0; }}
                    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 12px 16px; text-align: left; font-size: 14px; }}
                    th {{ background-color: #f8fafc; color: #475569; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; border-bottom: 2px solid #cbd5e1; }}
                    tr:last-child td {{ border-bottom: none; }}
                    tr:hover {{ background-color: #f1f5f9; }}
                    .btn-print {{ display: block; width: fit-content; margin: 0 auto 30px auto; padding: 12px 30px; background-color: #2563eb; color: white; text-align: center; text-decoration: none; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; border: none; transition: background-color 0.2s; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2); }}
                    .btn-print:hover {{ background-color: #1d4ed8; }}
                    @media print {{
                        .btn-print {{ display: none; }}
                        body {{ background-color: white; padding: 0; }}
                        .container {{ box-shadow: none; max-width: 100%; padding: 0; margin: 0; border-radius: 0; }}
                        .operario-section {{ break-inside: avoid; page-break-inside: avoid; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <button class="btn-print" onclick="window.print()">🖨️ Exportar a PDF / Imprimir</button>
                    
                    <div class="header">
                        <h1>Reporte Detallado - Actividades por Operario</h1>
                        <p class="fecha">Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    </div>
                    
                    {secciones_html}
                </div>
            </body>
            </html>
            """
            
            # Guardar el archivo HTML
            path_descargas = Path.home() / "Downloads"
            ruta_html = path_descargas / f"reporte_operarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(ruta_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            # Abrir en el navegador Default
            webbrowser.open(f'file://{str(ruta_html.resolve())}')
            messagebox.showinfo("Reporte Generado", f"El reporte de todos los operarios ha sido generado y abierto en su navegador web.\nDesde ahí puede guardarlo como PDF usando el botón integrado.\n\nUbicación: {ruta_html}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Ha ocurrido un error al generar el reporte de operarios: {str(e)}")


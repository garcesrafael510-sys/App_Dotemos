import tkinter as tk
from tkinter import ttk
import json
from gui.theme import COLOR_PRIMARIO, COLOR_BLANCO, FONT_TITULO, FONT_NORMAL
from src.data_loader import data_loader

class OperariosView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text="👥 Historial de Operarios", font=FONT_TITULO).pack(anchor='w')
        ttk.Label(header_frame, text="Registro histórico de las asignaciones y cargas de trabajo.", font=FONT_NORMAL).pack(anchor='w')

        # Tabla
        table_frame = ttk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        cols = ('ID Programación', 'Fecha', 'Operario', 'Asignaciones', 'Tiempo Asignado (min)')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=15)
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(side='left', fill='both', expand=True)

    def cargar_datos_historial(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        df = data_loader.obtener_historial_schedules()
        if df.empty:
            return
            
        for _, row in df.iterrows():
            id_prog = row['SCHEDULE_ID']
            fecha = row['FECHA_BALANCEO']
            resultado_json = row['RESULTADO_JSON']
            
            try:
                res = json.loads(resultado_json)
                actividades = res.get('actividades', [])
                
                ops_map = {}
                for act in actividades:
                    op = act[0]
                    t = float(act[4])
                    if op not in ops_map:
                        ops_map[op] = {'tareas': 0, 'tiempo': 0.0}
                    ops_map[op]['tareas'] += 1
                    ops_map[op]['tiempo'] += t
                    
                for op, datos in ops_map.items():
                    self.tree.insert("", "end", values=(id_prog.split('-')[0], fecha.split('.')[0], op, datos['tareas'], f"{datos['tiempo']:.2f}"))
            except Exception:
                continue

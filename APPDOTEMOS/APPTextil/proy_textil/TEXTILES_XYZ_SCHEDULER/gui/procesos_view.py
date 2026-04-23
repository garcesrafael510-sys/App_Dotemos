import tkinter as tk
from tkinter import ttk
import json
from gui.theme import COLOR_PRIMARIO, COLOR_BLANCO, FONT_TITULO, FONT_NORMAL
from src.data_loader import data_loader

class ProcesosView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text="⚙️ Historial de Procesos", font=FONT_TITULO).pack(anchor='w')
        ttk.Label(header_frame, text="Registro histórico del comportamiento de los procesos.", font=FONT_NORMAL).pack(anchor='w')

        table_frame = ttk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        cols = ('ID Programación', 'Fecha', 'Proceso', 'Veces Actividad', 'Carga Total (min)')
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
        if df.empty: return
            
        for _, row in df.iterrows():
            id_prog = row['SCHEDULE_ID']
            fecha = row['FECHA_BALANCEO']
            
            try:
                res = json.loads(row['RESULTADO_JSON'])
                actividades = res.get('actividades', [])
                
                procs_map = {}
                for act in actividades:
                    proc = act[2]
                    t = float(act[4])
                    if proc not in procs_map:
                        procs_map[proc] = {'veces': 0, 'tiempo': 0.0}
                    procs_map[proc]['veces'] += 1
                    procs_map[proc]['tiempo'] += t
                    
                for proc, datos in procs_map.items():
                    self.tree.insert("", "end", values=(id_prog.split('-')[0], fecha.split('.')[0], proc, datos['veces'], f"{datos['tiempo']:.2f}"))
            except Exception:
                continue

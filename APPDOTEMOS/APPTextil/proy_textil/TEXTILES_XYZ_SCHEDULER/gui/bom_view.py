# gui/bom_view.py (v5.3)
# Módulo para cargar, visualizar y gestionar el Bill of Materials (BOM).
# NOVEDAD v5.3: Añadido soporte para carga manual, edición y eliminación de operaciones.

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from src.data_loader import data_loader
from gui.theme import FONT_TITULO, FONT_SUBTITULO, FONT_NORMAL

class BomView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Título y Navegación ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', padx=20, pady=(10, 0))

        btn_home = ttk.Button(top_frame, text="< Volver",
                              command=lambda: controller.show_frame("LandingPage"))
        btn_home.pack(side='left')

        # --- Cabecera Principal ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=20, pady=20)

        title_label = ttk.Label(header_frame, text="Gestión de BOM", font=FONT_TITULO)
        title_label.pack(anchor='w')
        
        subtitle_label = ttk.Label(header_frame, text="Ver, agregar y gestionar operaciones de productos.", font=FONT_NORMAL)
        subtitle_label.pack(anchor='w')

        # --- Panel de Acciones ---
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(side='right', pady=(0, 10))

        btn_cargar = ttk.Button(actions_frame, text="Cargar CSV", command=self.cargar_bom_csv)
        btn_cargar.pack(side='left', padx=5)

        btn_añadir = ttk.Button(actions_frame, text="+ Añadir Operación", command=self.abrir_dialogo_operacion)
        btn_añadir.pack(side='left', padx=5)

        btn_borrar = ttk.Button(actions_frame, text="- Borrar Seleccionado", command=self.eliminar_operacion)
        btn_borrar.pack(side='left', padx=5)

        btn_guardar = ttk.Button(actions_frame, text="Guardar BOM", command=self.guardar_bom_manual)
        btn_guardar.pack(side='left', padx=5)

        # --- Tabla de Datos (Treeview) ---
        table_frame = ttk.Frame(self)
        table_frame.pack(expand=True, fill='both', padx=20, pady=10)

        # Definir columnas según el Excel del usuario
        self.columnas_display = ['Referencia', 'Descripción', 'Familia', 'Proceso', 'Consecutivo', 'Operación', 'Máquina', 'SAM (min)', 'Acciones']
        self.columnas_internas = ['REFERENCIA', 'DESCRIPCION', 'FAMILIA', 'PROCESO', 'CONSECUTIVO', 'OPERACION', 'MAQUINA', 'SAM-MINUTOS']

        self.tree_bom = ttk.Treeview(table_frame, columns=self.columnas_display, show='headings', height=15)
        
        # Configurar encabezados
        for col in self.columnas_display:
            self.tree_bom.heading(col, text=col)
            width = 100
            if col == 'Descripción': width = 150
            if col == 'Operación': width = 250
            if col == 'Acciones': width = 120
            self.tree_bom.column(col, width=width, anchor='center' if col in ['SAM (min)', 'Consecutivo'] else 'w')

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_bom.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree_bom.xview)
        self.tree_bom.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree_bom.pack(expand=True, fill='both')

        # Eventos
        self.tree_bom.bind("<Double-1>", self.al_doble_click)
        self.tree_bom.bind("<Delete>", lambda e: self.eliminar_operacion())
        
        # Menu contextual para acciones
        self.menu_contextual = tk.Menu(self, tearoff=0)
        self.menu_contextual.add_command(label="Editar", command=lambda: self.abrir_dialogo_operacion(self.tree_bom.selection()))
        self.menu_contextual.add_command(label="Eliminar", command=self.eliminar_operacion)
        self.tree_bom.bind("<Button-3>", self.mostrar_menu)

        # Cargar datos existentes
        self.cargar_bom_existente()

    def mostrar_menu(self, event):
        item = self.tree_bom.identify_row(event.y)
        if item:
            self.tree_bom.selection_set(item)
            self.menu_contextual.post(event.x_root, event.y_root)

    def cargar_bom_csv(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo BOM",
            filetypes=(("CSV Files", "*.csv"), ("All files", "*.*"))
        )
        if not filepath: return

        try:
            # Intentar leer con ; o ,
            df = pd.read_csv(filepath, sep=';', decimal=',')
            if len(df.columns) == 1:
                df = pd.read_csv(filepath, sep=',', decimal='.')

            df.columns = df.columns.str.strip().str.upper()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")
            return

        required_cols = ['REFERENCIA', 'DESCRIPCION', 'PROCESO', 'CONSECUTIVO', 'OPERACION', 'MAQUINA', 'SAM-MINUTOS']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            messagebox.showerror("Error", f"Faltan columnas requeridas: {', '.join(missing_cols)}")
            return

        # Normalizar nombres de columnas a mayúsculas para consistencia interna
        df.columns = [c.upper() for c in df.columns]
        
        self.controller.df_bom_full = df
        self.actualizar_vista_bom()
        messagebox.showinfo("Éxito", "BOM cargado localmente. Use 'Guardar BOM' para persistir los cambios.")

    def guardar_bom_manual(self):
        if self.controller.df_bom_full is None or self.controller.df_bom_full.empty:
            messagebox.showwarning("Aviso", "No hay datos para guardar.")
            return
        
        success, message = data_loader.guardar_bom(self.controller.df_bom_full)
        if success:
            messagebox.showinfo("Éxito", message)
            self.actualizar_mapa_referencias_controlador()
        else:
            messagebox.showerror("Error", message)

    def abrir_dialogo_operacion(self, item_id=None):
        """Abre una ventana para añadir o editar una operación."""
        if isinstance(item_id, (list, tuple)) and len(item_id) > 0:
            item_id = item_id[0]
            
        titulo = "Editar Operación" if item_id else "Añadir Operación"
        dialogo = tk.Toplevel(self)
        dialogo.title(titulo)
        dialogo.geometry("450x650")
        dialogo.resizable(False, False)
        dialogo.grab_set()

        # Valores iniciales
        valores = ["", "", "", "", "", "", "", "0.0"]
        if item_id:
            item_data = self.tree_bom.item(item_id, "values")
            valores = list(item_data[:8])

        # Formulario
        campos = ["Referencia:", "Descripción:", "Familia:", "Proceso:", "Consecutivo:", "Operación:", "Máquina:", "SAM (min):"]
        entries = []

        main_frame = ttk.Frame(dialogo, padding=20)
        main_frame.pack(fill='both', expand=True)

        for i, campo in enumerate(campos):
            ttk.Label(main_frame, text=campo, font=FONT_NORMAL).pack(pady=(5, 0), anchor='w')
            entry = ttk.Entry(main_frame, font=FONT_NORMAL, width=40)
            entry.insert(0, valores[i])
            entry.pack(pady=5)
            entries.append(entry)

        def guardar_cambios():
            nv = [e.get().strip() for e in entries]
            if not nv[0] or not nv[5]:
                messagebox.showwarning("Faltan datos", "Referencia y Operación son obligatorios.")
                return
            
            try:
                sam_val = float(nv[7].replace(',', '.'))
                cons_val = int(nv[4]) if nv[4] else 0
            except ValueError:
                messagebox.showwarning("Error", "SAM debe ser número y Consecutivo entero.")
                return

            row_dict = {
                'REFERENCIA': nv[0], 'DESCRIPCION': nv[1], 'FAMILIA': nv[2],
                'PROCESO': nv[3], 'CONSECUTIVO': cons_val, 'OPERACION': nv[5],
                'MAQUINA': nv[6], 'SAM-MINUTOS': sam_val
            }

            if self.controller.df_bom_full is None:
                self.controller.df_bom_full = pd.DataFrame(columns=self.columnas_internas)

            if item_id:
                idx = self.tree_bom.index(item_id)
                for col, val in row_dict.items():
                    if col in self.controller.df_bom_full.columns:
                        self.controller.df_bom_full.iloc[idx, self.controller.df_bom_full.columns.get_loc(col)] = val
            else:
                new_row = pd.DataFrame([row_dict])
                self.controller.df_bom_full = pd.concat([self.controller.df_bom_full, new_row], ignore_index=True)

            self.actualizar_vista_bom()
            dialogo.destroy()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Cancelar", command=dialogo.destroy).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Guardar", command=guardar_cambios).pack(side='left', padx=10)

    def eliminar_operacion(self):
        item_id = self.tree_bom.selection()
        if not item_id: return
        
        if messagebox.askyesno("Confirmar", "¿Eliminar esta operación?"):
            idx = self.tree_bom.index(item_id[0])
            self.controller.df_bom_full = self.controller.df_bom_full.drop(self.controller.df_bom_full.index[idx]).reset_index(drop=True)
            self.actualizar_vista_bom()

    def al_doble_click(self, event):
        item_id = self.tree_bom.identify_row(event.y)
        if item_id:
            self.abrir_dialogo_operacion(item_id)

    def actualizar_vista_bom(self):
        for i in self.tree_bom.get_children(): self.tree_bom.delete(i)
        df = self.controller.df_bom_full
        if df is None or df.empty: return

        for _, row in df.iterrows():
            valores = [
                row.get('REFERENCIA', ''), row.get('DESCRIPCION', ''),
                row.get('FAMILIA', ''), row.get('PROCESO', ''),
                row.get('CONSECUTIVO', ''), row.get('OPERACION', ''),
                row.get('MAQUINA', ''), row.get('SAM-MINUTOS', 0.0),
                "Editar / Eliminar"
            ]
            self.tree_bom.insert("", "end", values=valores)
            
    def cargar_bom_existente(self):
        df = data_loader.obtener_bom_completo()
        if df is not None and not df.empty:
            df = df.rename(columns={'CONSECUTIVO_OPERACION': 'CONSECUTIVO', 'SAM_MINUTOS': 'SAM-MINUTOS'})
            self.controller.df_bom_full = df
            self.actualizar_vista_bom()
            self.actualizar_mapa_referencias_controlador()

    def actualizar_mapa_referencias_controlador(self):
        df = self.controller.df_bom_full
        if df is not None and not df.empty:
            if 'REFERENCIA' in df.columns and 'DESCRIPCION' in df.columns:
                self.controller.referencia_nombre_map = df.drop_duplicates('REFERENCIA').set_index('REFERENCIA')['DESCRIPCION'].to_dict()

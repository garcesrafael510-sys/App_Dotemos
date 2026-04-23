# gui/orders_view.py (v5.3)
# Módulo para crear, visualizar y gestionar órdenes de producción.
# NOVEDAD v5.3: Nueva interfaz tipo dashboard con soporte para Clientes, Fechas y Prioridad.

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from src.data_loader import data_loader
from gui.theme import FONT_TITULO, FONT_SUBTITULO, FONT_NORMAL
from datetime import datetime

class OrdersView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Cabecera Principal ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=20, pady=20)

        btn_home = ttk.Button(header_frame, text="< Volver",
                              command=lambda: controller.show_frame("LandingPage"))
        btn_home.pack(side='top', anchor='nw')

        title_label = ttk.Label(header_frame, text="Órdenes de Producción", font=FONT_TITULO)
        title_label.pack(anchor='w', pady=(10, 0))
        
        subtitle_label = ttk.Label(header_frame, text="Crear y gestionar órdenes de clientes.", font=FONT_NORMAL)
        subtitle_label.pack(anchor='w')

        # --- Panel de Acciones ---
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(side='right', pady=(0, 10))

        btn_añadir = ttk.Button(actions_frame, text="+ Añadir Orden", command=self.abrir_dialogo_orden)
        btn_añadir.pack(side='left', padx=5)

        btn_importar = ttk.Button(actions_frame, text="📥 Importar Archivo", command=self.importar_ordenes_archivo)
        btn_importar.pack(side='left', padx=5)

        btn_actualizar = ttk.Button(actions_frame, text="Actualizar Lista", command=self.cargar_ordenes_db)
        btn_actualizar.pack(side='left', padx=5)

        # --- Tabla de Órdenes (Treeview) ---
        table_frame = ttk.Frame(self)
        table_frame.pack(expand=True, fill='both', padx=20, pady=10)

        # Columnas según la imagen del usuario
        self.columnas = ['ID Orden', 'Cliente', 'Referencia', 'Descripción', 'Cantidad', 'Fecha Entrega', 'Prioridad', 'Estado']
        
        self.tree_ordenes = ttk.Treeview(table_frame, columns=self.columnas, show='headings', height=15)
        
        for col in self.columnas:
            self.tree_ordenes.heading(col, text=col)
            width = 120
            if col == 'ID Orden': width = 180
            if col == 'Descripción': width = 200
            self.tree_ordenes.column(col, width=width, anchor='center' if col in ['Cantidad', 'Prioridad', 'Estado'] else 'w')

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_ordenes.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree_ordenes.xview)
        self.tree_ordenes.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree_ordenes.pack(expand=True, fill='both')

        # Eventos
        self.tree_ordenes.bind("<Button-3>", self.mostrar_menu_contextual)

        # Cargar datos al iniciar
        self.cargar_ordenes_db()

    def mostrar_menu_contextual(self, event):
        item = self.tree_ordenes.identify_row(event.y)
        if item:
            self.tree_ordenes.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Eliminar Orden", command=self.eliminar_orden)
            menu.add_command(label="Editar Orden", command=self.editar_orden)
            menu.post(event.x_root, event.y_root)

    def editar_orden(self):
        selection = self.tree_ordenes.selection()
        if not selection: return
        op_id = self.tree_ordenes.item(selection[0], 'values')[0]
        
        # Buscar la orden completa en la DB
        df_log = data_loader.obtener_orders_log()
        orden_row = df_log[df_log['OP_UNIQUE_ID'] == op_id]
        if orden_row.empty: return
        
        row = orden_row.iloc[0]
        detalle_df = data_loader.obtener_detalle_orden(op_id)
        items = detalle_df.to_dict('records') if not detalle_df.empty else []
        
        self.abrir_dialogo_orden(op_id, row.get('CLIENTE'), row.get('FECHA_ENTREGA'), row.get('PRIORIDAD'), items)

    def eliminar_orden(self):
        selection = self.tree_ordenes.selection()
        if not selection: return
        
        op_id = self.tree_ordenes.item(selection[0], 'values')[0]
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la orden {op_id}?"):
            data_loader.borrar_orden_por_id(op_id)
            self.cargar_ordenes_db()

    def cargar_ordenes_db(self, event=None):
        """Carga todas las órdenes de la DB."""
        for i in self.tree_ordenes.get_children():
            self.tree_ordenes.delete(i)
            
        df_log = data_loader.obtener_orders_log()
        if df_log is None or df_log.empty:
            return

        for _, row in df_log.iterrows():
            op_id = row['OP_UNIQUE_ID']
            cliente = row.get('CLIENTE') or 'N/A'
            fecha_e = row.get('FECHA_ENTREGA') or 'N/A'
            prioridad = row.get('PRIORIDAD') if pd.notnull(row.get('PRIORIDAD')) else 3
            estado = row.get('ESTADO') or 'Pendiente'
            
            # Cargar items del JSON para mostrar el primer item o un resumen
            items_df = data_loader.obtener_detalle_orden(op_id)
            if items_df is not None and not items_df.empty:
                for _, item in items_df.iterrows():
                    ref = item.get('REFERENCIA', 'N/A')
                    desc = self.controller.referencia_nombre_map.get(ref, 'N/A')
                    cant = item.get('CANTIDAD', 0)
                    
                    self.tree_ordenes.insert("", "end", values=(
                        op_id, cliente, ref, desc, cant, fecha_e, prioridad, estado
                    ))
            else:
                self.tree_ordenes.insert("", "end", values=(
                    op_id, cliente, "N/A", "Sin items", 0, fecha_e, prioridad, estado
                ))

    def actualizar_lista_ordenes(self):
        self.cargar_ordenes_db()

    def importar_ordenes_archivo(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de órdenes",
            filetypes=(
                ("Archivos Soportados (Excel/CSV)", "*.xlsx *.xls *.csv"),
                ("Archivos CSV", "*.csv"),
                ("Archivos Excel", "*.xlsx *.xls"),
                ("Todos los archivos", "*.*")
            )
        )
        if not filepath:
            return

        try:
            if filepath.lower().endswith('.csv'):
                try:
                    df = pd.read_csv(filepath, sep=';', encoding='utf-8')
                    if len(df.columns) < 3: # Maybe it's comma separated
                        df = pd.read_csv(filepath, sep=',', encoding='utf-8')
                except Exception:
                    df = pd.read_csv(filepath, sep=',', encoding='utf-8')
            else:
                df = pd.read_excel(filepath)
            
            # Normalizar nombres de columnas a minúsculas
            col_map = {str(col).strip().lower(): col for col in df.columns}
            
            # Buscar mapeo inteligente
            req_mapping = {}
            for req in ['id', 'cliente', 'referencia', 'cantidad', 'fecha', 'prioridad']:
                encontrada = next((c for c in col_map if req in c), None)
                req_mapping[req] = col_map[encontrada] if encontrada else None

            # Validación estricta
            if not req_mapping['id'] or not req_mapping['referencia'] or not req_mapping['cantidad']:
                messagebox.showerror("Error", "Faltan columnas necesarias en el archivo.\nSe requiere al menos:\n- ID\n- Referencia\n- Cantidad")
                return

            ordenes_agrupadas = df.groupby(req_mapping['id'])
            contador_exito = 0
            
            for op_id, group in ordenes_agrupadas:
                if pd.isna(op_id): continue
                op_id = str(op_id).strip()
                
                # Extraer metadatos comunes de la primera iteración
                primera_fila = group.iloc[0]
                
                cliente = "N/A"
                if req_mapping['cliente'] and pd.notna(primera_fila[req_mapping['cliente']]):
                    cliente = str(primera_fila[req_mapping['cliente']]).strip()
                
                fecha = datetime.now().strftime("%Y-%m-%d")
                if req_mapping['fecha'] and pd.notna(primera_fila[req_mapping['fecha']]):
                    val_fecha = primera_fila[req_mapping['fecha']]
                    if isinstance(val_fecha, pd.Timestamp):
                        fecha = val_fecha.strftime("%Y-%m-%d")
                    elif isinstance(val_fecha, datetime):
                        fecha = val_fecha.strftime("%Y-%m-%d")
                    else:
                        fecha = str(val_fecha).split(' ')[0] # Remueve la hora si viene como texto
                
                prioridad = 3
                if req_mapping['prioridad'] and pd.notna(primera_fila[req_mapping['prioridad']]):
                    try:
                        prioridad = int(float(primera_fila[req_mapping['prioridad']]))
                    except ValueError:
                        pass
                
                # Recopilar items
                items = []
                for _, row in group.iterrows():
                    ref = str(row[req_mapping['referencia']]).strip()
                    try:
                        cant = int(float(row[req_mapping['cantidad']]))
                    except (ValueError, TypeError):
                        cant = 0
                    if ref and cant > 0:
                        items.append({'REFERENCIA': ref, 'CANTIDAD': cant})
                
                if items:
                    data_loader.guardar_orden(op_id, cliente, fecha, prioridad, items)
                    contador_exito += 1
            
            messagebox.showinfo("Importación Exitosa", f"Se han importado {contador_exito} órdenes desde el archivo.")
            self.cargar_ordenes_db()

        except Exception as e:
            messagebox.showerror("Error de Importación", f"Ocurrió un error al procesar el archivo:\n{str(e)}")

    def abrir_dialogo_orden(self, edit_op_id=None, e_cliente="", e_fecha="", e_prioridad=3, e_items=None):
        """Abre ventana para crear o editar una orden."""
        titulo = "Editar Orden de Producción" if edit_op_id else "Nueva Orden de Producción"
        dialogo = tk.Toplevel(self)
        dialogo.title(titulo)
        dialogo.geometry("600x650")
        dialogo.resizable(False, False)
        dialogo.grab_set()

        # Si no hay fecha, poner la de hoy
        if not e_fecha: e_fecha = datetime.now().strftime("%Y-%m-%d")
        if e_items is None: e_items = []

        # --- Encabezado de la Orden ---
        header = ttk.LabelFrame(dialogo, text="Datos del Cliente y Entrega", padding=10)
        header.pack(fill='x', padx=20, pady=10)

        ttk.Label(header, text="Cliente:").grid(row=0, column=0, sticky='w')
        ent_cliente = ttk.Entry(header, width=40)
        ent_cliente.insert(0, e_cliente)
        ent_cliente.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(header, text="Fecha Entrega (AAAA-MM-DD):").grid(row=1, column=0, sticky='w')
        ent_fecha = ttk.Entry(header, width=40)
        ent_fecha.insert(0, e_fecha)
        ent_fecha.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(header, text="Prioridad (1-5):").grid(row=2, column=0, sticky='w')
        spn_prioridad = tk.Spinbox(header, from_=1, to=5, width=5)
        spn_prioridad.delete(0, "end")
        spn_prioridad.insert(0, str(e_prioridad))
        spn_prioridad.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # --- Selector de Productos ---
        prod_frame = ttk.LabelFrame(dialogo, text="Añadir Productos a la Orden", padding=10)
        prod_frame.pack(fill='x', padx=20, pady=5)

        ttk.Label(prod_frame, text="Referencia:").grid(row=0, column=0, sticky='w')
        refs = sorted(list(self.controller.referencia_nombre_map.keys()))
        combo_ref = ttk.Combobox(prod_frame, values=refs, width=25)
        combo_ref.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(prod_frame, text="Cantidad:").grid(row=0, column=2, sticky='w', padx=10)
        ent_cant = ttk.Entry(prod_frame, width=10)
        ent_cant.grid(row=0, column=3, padx=5, pady=5)

        items_en_creacion = e_items.copy()

        # Tabla temporal de items
        tree_temp = ttk.Treeview(dialogo, columns=('Ref', 'Cant'), show='headings', height=5)
        tree_temp.heading('Ref', text='Referencia')
        tree_temp.heading('Cant', text='Cantidad')
        tree_temp.column('Ref', width=200)
        tree_temp.column('Cant', width=100)
        tree_temp.pack(fill='both', padx=20, pady=10)
        
        # Poblar si estamos editando
        for item in items_en_creacion:
            tree_temp.insert("", "end", values=(item['REFERENCIA'], item['CANTIDAD']))

        def add_item():
            ref = combo_ref.get()
            cant = ent_cant.get()
            if ref and cant:
                try:
                    items_en_creacion.append({'REFERENCIA': ref, 'CANTIDAD': int(cant)})
                    tree_temp.insert("", "end", values=(ref, cant))
                    combo_ref.set('')
                    ent_cant.delete(0, tk.END)
                except ValueError:
                    messagebox.showwarning("Error", "Cantidad debe ser un número.")

        ttk.Button(prod_frame, text="Agregar Item", command=add_item).grid(row=1, column=0, columnspan=4, pady=5)

        def finalizar_orden():
            cliente = ent_cliente.get().strip()
            fecha = ent_fecha.get().strip()
            prioridad_val = spn_prioridad.get()
            if not cliente or not items_en_creacion:
                messagebox.showwarning("Incompleto", "Debe ingresar un cliente y al menos un producto.")
                return
            
            op_id = edit_op_id if edit_op_id else f"ORD-{int(datetime.now().timestamp())}"
            data_loader.guardar_orden(op_id, cliente, fecha, int(prioridad_val), items_en_creacion)
            
            messagebox.showinfo("Éxito", f"Orden {op_id} guardada correctamente.")
            self.cargar_ordenes_db()
            dialogo.destroy()

        ttk.Button(dialogo, text="GUARDAR ÓRDEN", command=finalizar_orden).pack(pady=20)

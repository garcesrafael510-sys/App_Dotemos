# src/report_generator.py (Versión v2.1 - Generación de Reporte en PDF)
from fpdf import FPDF
import os
import tempfile
from src.gantt_utils import generar_gantt
from datetime import datetime

class PDFReport(FPDF):
    """
    Clase que extiende FPDF para generar el informe de balanceo.
    """
    
    # Constantes
    COL_WIDTH = 45
    LINE_HEIGHT = 7
    FONT_SIZE = 10

    def header(self):
        # Encabezado: Título y Fecha
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Informe de Programación y Balanceo - Textiles XYZ', 0, 1, 'C')
        self.set_font('Arial', '', 9)
        self.cell(0, 5, f'Generado el: {self._get_fecha_actual()}', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, title, 0, 1, 'L', fill=True)
        self.ln(4)

    def _get_fecha_actual(self):
        """Retorna la fecha y hora actual formateada."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def create_summary_page(self, productos_info, balanceo_info):
        self.add_page()
        self.chapter_title(f"Resumen de la Orden de Producción (OP: {balanceo_info.get('OP_ID', 'N/A')})")

        # --- Sección 1: Datos Generales de la Orden ---
        self.set_font('Arial', 'B', self.FONT_SIZE)
        self.set_fill_color(240, 240, 240)
        
        # Fila 1
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, "Referencia(s):", border=1, fill=True)
        self.set_font('Arial', '', self.FONT_SIZE)
        self.cell(0, self.LINE_HEIGHT, productos_info.get('referencia', 'N/A'), border=1, ln=1)
        
        # Fila 2
        self.set_font('Arial', 'B', self.FONT_SIZE)
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, "Cantidad Total Lote:", border=1, fill=True)
        self.set_font('Arial', '', self.FONT_SIZE)
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, str(productos_info.get('cantidad', 'N/A')), border=1, fill=False)
        
        self.set_font('Arial', 'B', self.FONT_SIZE)
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, "SAM Unitario Global:", border=1, fill=True)
        self.set_font('Arial', '', self.FONT_SIZE)
        self.cell(0, self.LINE_HEIGHT, productos_info.get('sam_global', 'N/A'), border=1, ln=1)
        
        self.ln(8)

        # --- Sección 2: Resultados del Balanceo (KPIs) ---
        self.chapter_title("Métricas de Balanceo y Productividad")

        # Fila 1 (Carga Máxima vs. Teórica)
        self.set_font('Arial', 'B', self.FONT_SIZE)
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, "Tiempo Total del Lote:", border=1, fill=True)
        self.set_font('Arial', '', self.FONT_SIZE)
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, balanceo_info.get('Tiempo Total Lote', 'N/A'), border=1, fill=False)

        self.set_font('Arial', 'B', self.FONT_SIZE)
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, "Carga Máxima (C_max):", border=1, fill=True)
        self.set_font('Arial', '', self.FONT_SIZE)
        self.cell(0, self.LINE_HEIGHT, balanceo_info.get('Carga Maxima (C_max)', 'N/A'), border=1, ln=1)

        # Fila 2 (Eficiencia y Días)
        self.set_font('Arial', 'B', self.FONT_SIZE)
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, "Eficiencia de Balanceo:", border=1, fill=True)
        self.set_font('Arial', 'B', self.FONT_SIZE) # Usar negrita para el KPI
        self.set_text_color(20, 100, 20) # Color verde
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, balanceo_info.get('Eficiencia', 'N/A'), border=1, fill=False)
        self.set_text_color(0, 0, 0) # Volver a negro
        
        self.set_font('Arial', 'B', self.FONT_SIZE)
        self.cell(self.COL_WIDTH, self.LINE_HEIGHT, "Días Proyectados (8h):", border=1, fill=True)
        self.set_font('Arial', '', self.FONT_SIZE)
        self.cell(0, self.LINE_HEIGHT, balanceo_info.get('Dias Proyectados', 'N/A'), border=1, ln=1)
        
        self.ln(5)

    def table_asignaciones(self, operario_id, tareas):
        """Genera una tabla detallada de asignaciones para un operario."""
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(220, 220, 255) # Fondo azul claro
        self.cell(0, 8, f"Operario {operario_id}", 1, 1, 'L', fill=True)

        # Cabecera de la tabla de tareas
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(240, 240, 240)
        self.cell(20, 8, "Sec.", 1, 0, 'C', fill=True)
        self.cell(120, 8, "Operación", 1, 0, 'C', fill=True)
        self.cell(40, 8, "Tiempo (min)", 1, 1, 'C', fill=True)

        # Contenido de la tabla
        self.set_font('Arial', '', 9)
        total_carga = 0
        for i, tarea in enumerate(tareas, 1):
            self.cell(20, self.LINE_HEIGHT, str(i), 1, 0, 'C')
            
            # Usar MultiCell para el texto largo
            x = self.get_x()
            y = self.get_y()
            
            # Altura calculada para MultiCell (asumiendo 3 líneas máximo)
            h_multi = self.LINE_HEIGHT
            
            self.multi_cell(120, h_multi, tarea['descripcion'], 1, 'L', fill=False)
            
            # Regresar a la posición y altura correctas
            self.set_xy(x + 120, y) 
            self.cell(40, self.LINE_HEIGHT, f"{tarea['minutos_asignados']:.2f}", 1, 1, 'R')
            total_carga += tarea['minutos_asignados']
        
        # Fila de Total
        self.set_font('Arial', 'B', 10)
        self.cell(140, 8, "TOTAL CARGA:", 1, 0, 'R')
        self.cell(40, 8, f"{total_carga:.2f}", 1, 1, 'R')
        self.ln(5)

    def create_gantt_chart(self, asignaciones):
        """Inserta el gráfico de Gantt generado por Matplotlib."""
        self.chapter_title("Secuenciación Detallada y Diagrama de Gantt")
        
        # Generar imagen temporal del Gantt
        gantt_path = generar_gantt(asignaciones, para_pdf=True)
        
        # Insertar la imagen en el PDF
        self.image(gantt_path, x=10, w=180) 
        self.ln(5)
        
        # Eliminar el archivo temporal
        os.remove(gantt_path)
        
    @staticmethod
    def generate_report(balanceo_info: dict, productos_info: dict, asignaciones: dict) -> str:
        """Método estático para generar el PDF completo y retornar la ruta."""
        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Generar primera página de resumen
        pdf.create_summary_page(productos_info, balanceo_info)
        
        # Generar el Gantt
        pdf.create_gantt_chart(asignaciones)

        # Generar páginas INVIDIDUALES (Tickets) por operario
        operarios = sorted(asignaciones.keys(), key=lambda x: int(x))
        for op_id in operarios:
            pdf.add_page() # <-- CLAVE: Una hoja nueva para cada operario
            pdf.chapter_title(f"Planilla de Piso - Operario {op_id}")
            
            # Encabezado Operativo
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f"Orden de Producción: {balanceo_info.get('OP_ID', 'N/A')}", 0, 1)
            pdf.cell(0, 5, f"Fecha de Ejecución: {pdf._get_fecha_actual()}", 0, 1)
            pdf.ln(5)

            tareas = asignaciones[op_id]
            pdf.table_asignaciones(op_id, tareas)

        # Guardar el PDF en una ubicación temporal y retornar la ruta
        temp_dir = tempfile.gettempdir()
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = os.path.join(temp_dir, f"informe_balanceo_{balanceo_info.get('OP_ID', date_str)}_preview.pdf")
        pdf.output(pdf_path, 'F')
        return pdf_path

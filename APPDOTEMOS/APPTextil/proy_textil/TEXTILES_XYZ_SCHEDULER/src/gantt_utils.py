# src/gantt_utils.py (Versión v2.1 - Generación de Gráfico de Gantt)
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import os

def generar_gantt(asignaciones, nombres_operaciones=None, para_pdf=False):
    """
    Genera un gráfico de Gantt enfocado en la secuencia de Tareas.
    Eje Y = Tareas, Eje X = Tiempo. Colores = Operarios.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Ajustar margen izquierdo para que no se corten los nombres largos
    plt.subplots_adjust(left=0.35)
    
    tareas_timeline = []
    tareas_unicas = []
    
    # Acumular el tiempo continuamente a lo largo de TODA la ruta de producción
    tiempo_inicio_global = 0
    
    # 1. Extraer todas las tareas y calcular los tiempos de inicio/duración
    # Asegurar el orden numérico de los operarios para la secuencia lógica
    for operario_id in sorted(list(asignaciones.keys()), key=lambda x: int(x)):
        tareas = asignaciones[operario_id]
        for tarea in tareas:
            t_asignado = tarea['minutos_asignados']
            # Quitar el ID de producto para que el nombre de la tarea sea más limpio
            desc_completa = tarea.get('descripcion', 'Operación')
            desc = desc_completa.split(' - ')[-1] if ' - ' in desc_completa else desc_completa
            
            if desc not in tareas_unicas:
                tareas_unicas.append(desc)
                
            tareas_timeline.append({
                'operario': operario_id,
                'tarea': desc,
                'inicio': tiempo_inicio_global,
                'duracion': t_asignado
            })
            tiempo_inicio_global += t_asignado
            
    # Invertir para que la primera tarea salga arriba en el gráfico
    tareas_unicas.reverse()
    
    # 2. Generar mapa de colores por operario
    operarios_unicos = sorted(list(asignaciones.keys()))
    colors = plt.cm.tab10(np.linspace(0, 1, max(10, len(operarios_unicos))))
    color_map = {op: colors[i % 10] for i, op in enumerate(operarios_unicos)}

    # 3. Dibujar las barras
    for item in tareas_timeline:
        y_pos = tareas_unicas.index(item['tarea'])
        ax.barh(y_pos, item['duracion'], left=item['inicio'], 
                color=color_map[item['operario']], edgecolor='black', align='center', alpha=0.85)
        
        # Etiqueta del operario dentro de la barra si es lo suficientemente ancha
        if item['duracion'] > (max([t['inicio'] + t['duracion'] for t in tareas_timeline]) * 0.05):
            ax.text(item['inicio'] + item['duracion']/2, y_pos, 
                    f"Op {item['operario']}", va='center', ha='center', fontsize=8, color='white', fontweight='bold')

    # 4. Configurar Ejes y Leyenda
    ax.set_yticks(range(len(tareas_unicas)))
    
    # Truncar textos muy largos en el eje Y
    truncated_labels = [(t[:30] + '..') if len(t) > 30 else t for t in tareas_unicas]
    ax.set_yticklabels(truncated_labels, fontsize=8)
    
    ax.set_xlabel("Tiempo (minutos)")
    ax.set_title("Diagrama de Gantt - Flujo de Tareas de la Orden")
    
    # Leyenda
    import matplotlib.patches as mpatches
    legend_patches = [mpatches.Patch(color=color_map[op], label=f'Operario {op}') for op in operarios_unicos]
    
    # Posicionar leyenda fuera del gráfico
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])
    ax.legend(handles=legend_patches, loc='center left', bbox_to_anchor=(1, 0.5), title="Asignación")

    ax.grid(axis='x', linestyle='--', alpha=0.6)
    
    if para_pdf:
        # Guarda temporalmente la imagen y retorna la ruta
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"gantt_{os.getpid()}.png")
        fig.savefig(file_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return file_path
    else:
        # Retorna la figura para incrustar en Tkinter
        return fig

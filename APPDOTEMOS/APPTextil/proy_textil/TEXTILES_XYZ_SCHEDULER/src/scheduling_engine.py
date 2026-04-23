# scheduling_engine.py (Versión v3.0 - Lógica de Balanceo Heurístico Secuencial)
# Implementa la nueva lógica de balanceo basada en reglas y asignación secuencial.

import pandas as pd
from typing import Dict, Any, List
from src.data_loader import data_loader

def calcular_datos_iniciales(
    orden_detalle_df: pd.DataFrame,
    numero_operarios: int
) -> Dict[str, Any]:
    """
    Punto 4: Prepara el DataFrame inicial con los cálculos de producción
    y la tabla base para el balanceo, basado en LA CANTIDAD REAL de la orden.
    """
    if orden_detalle_df is None or orden_detalle_df.empty:
        return {"error": "El detalle de la orden está vacío."}

    all_items_data = []
    indicadores_produccion = []
    
    # Procesar cada ítem (producto) en la orden de forma secuencial
    for index, row in orden_detalle_df.iterrows():
        try:
            referencia = str(row['REFERENCIA'])
            cantidad = int(row.get('CANTIDAD', 0))

            df_bom = data_loader.obtener_bom_por_referencia(referencia)
            if df_bom is None or df_bom.empty:
                continue

            # --- 1. RESOLUCIÓN DE NOMBRE (Punto 3 del requerimiento) ---
            # Prioridad: Columna explícita en la orden -> Columna DESCRIPCION en BOM -> Referencia
            nombre_producto = str(row.get('DESCRIPCION', 
                                   row.get('NOMBRE_DISPLAY', 
                                   df_bom.iloc[0].get('DESCRIPCION', referencia))))

            # --- 2. Cálculos de Producción por Producto ---
            sam_total_producto = float(df_bom['SAM-MINUTOS'].sum())
            
            # El tiempo total necesario para terminar la orden de este producto
            tiempo_total_requerido = sam_total_producto * cantidad

            if tiempo_total_requerido == 0:
                unidades_por_hora = 0.0
            else:
                # Si esto fuera un ritmo continuo en un turno estándar:
                unidades_por_hora = float(60 / sam_total_producto) * numero_operarios

            unidades_por_dia = unidades_por_hora * 8

            indicadores_produccion.append({
                "Referencia": str(referencia),
                "Nombre": str(nombre_producto),
                "Cantidad": str(cantidad),
                "SAM Total Producto": f"{sam_total_producto:.2f} min",
                "Tiempo Total Requerido": f"{tiempo_total_requerido:.2f} min",
                "Unidades por Hora (Ritmo Bruto)": f"{unidades_por_hora:.2f}"
            })

            # --- 3. Tabla de Datos a Generar ---
            df_bom['codigo_producto'] = referencia
            df_bom['nombre_producto'] = nombre_producto
            
            if 'PROCESO' not in df_bom.columns:
                df_bom['PROCESO'] = 'ENSAMBLE'
                
            proceso_order = {'ENSAMBLE': 0, 'TERMINACION': 1, 'GENERAL': 2}
            df_bom['proceso_rank'] = df_bom['PROCESO'].map(lambda x: proceso_order.get(str(x).upper(), 99))
            df_bom = df_bom.sort_values(by=['proceso_rank', 'CONSECUTIVO'], ascending=[True, True])
            
            df_bom['No secuencia'] = df_bom['CONSECUTIVO']
            df_bom['id'] = df_bom['codigo_producto'].astype(str) + '_' + df_bom['PROCESO'].astype(str) + '_' + df_bom['No secuencia'].astype(str)
            df_bom['Sam min operacion'] = df_bom['SAM-MINUTOS'].astype(float)
            
            # CLAVE: Asignar el tiempo necesario EXACTO para todo el lote
            df_bom['tiempo_necesario'] = df_bom['SAM-MINUTOS'] * cantidad
            
            item_data = df_bom[[
                'id', 'codigo_producto', 'nombre_producto', 'PROCESO', 'No secuencia', 
                'OPERACION', 'MAQUINA', 'Sam min operacion', 'tiempo_necesario'
            ]]
            all_items_data.append(item_data)
        except Exception as e:
            # Si un producto falla, lo saltamos pero guardamos el error
            print(f"Error procesando producto {row.get('REFERENCIA')}: {e}")
            continue

    if not all_items_data:
        refs_buscadas = orden_detalle_df['REFERENCIA'].tolist()
        refs_str = ", ".join(map(str, refs_buscadas))
        return {"error": f"BOM faltante para referencias: {refs_str}. Verifique la Gestión de BOM."}

    # Consolidar la tabla de todos los productos
    df_final_balanceo = pd.concat(all_items_data, ignore_index=True)

    # Añadir columnas de operarios dinámicamente
    for i in range(1, numero_operarios + 1):
        df_final_balanceo[f'operario_{i}'] = 0.0

    return {
        "tabla_datos_iniciales": df_final_balanceo,
        "indicadores_produccion": indicadores_produccion,
    }


def balanceo_heuristico_secuencial(
    df_datos_iniciales: pd.DataFrame,
    numero_operarios: int,
    tiempo_limite_min: int
) -> Dict[str, Any]:
    

    cols_needed = ['id', 'codigo_producto', 'nombre_producto', 'PROCESO', 'No secuencia', 
                  'OPERACION', 'MAQUINA', 'Sam min operacion', 'tiempo_necesario']
    df_asignacion = df_datos_iniciales[cols_needed].copy()

    # Reiniciar columnas de operarios
    for i in range(numero_operarios):
        df_asignacion[f'operario_{i+1}'] = 0.0

    # Inicializar cargas de operarios
    cargas_operarios = {f'operario_{i+1}': 0.0 for i in range(numero_operarios)}
        
    idx_operario_actual = 0
    
    # Iterar sobre cada fila (operación) de la tabla, respetando el orden real
    for index, row in df_asignacion.iterrows():
        tiempo_op_necesario = row['tiempo_necesario']
        
        # Continuar asignando el tiempo de esta operación hasta que se agote
        while tiempo_op_necesario > 0.001: 
            if idx_operario_actual >= numero_operarios:
                # Escenario: Faltan operarios
                return {
                    "error": f"Operarios insuficientes. Se requiere más capacidad para asignar la operación '{row['OPERACION']}'.",
                    "df_resultado": df_asignacion,
                    "kpis": None
                }

            nombre_col_operario = f'operario_{idx_operario_actual + 1}'
            # Calculamos la capacidad disponible en la canasta de este operario
            tiempo_disponible_operario = tiempo_limite_min - cargas_operarios[nombre_col_operario]

            if tiempo_disponible_operario > 0:
                # Asignamos el mínimo entre lo que falta de la operacion y lo que le sobra al operario
                tiempo_a_asignar = min(tiempo_op_necesario, tiempo_disponible_operario)
                
                df_asignacion.at[index, nombre_col_operario] += tiempo_a_asignar
                cargas_operarios[nombre_col_operario] += tiempo_a_asignar
                tiempo_op_necesario -= tiempo_a_asignar
            
            # Si a este operario ya no le queda tiempo disponible, pasamos al siguiente
            if (tiempo_limite_min - cargas_operarios[nombre_col_operario]) <= 0.001:
                idx_operario_actual += 1

    # --- Cálculo de KPIs Internos (Punto 6) ---
    tiempo_total_disponible = numero_operarios * tiempo_limite_min
    tiempo_total_asignado = sum(cargas_operarios.values())
    
    if tiempo_total_disponible > 0:
        porcentaje_asignacion_total = (tiempo_total_asignado / tiempo_total_disponible) * 100
    else:
        porcentaje_asignacion_total = 0

    kpis = {
        "Carga por Operario (min)": {op: round(carga, 2) for op, carga in cargas_operarios.items()},
        "Tiempo Total Asignado (min)": f"{tiempo_total_asignado:.2f}",
        "Tiempo Total Disponible (min)": f"{tiempo_total_disponible:.2f}",
        "% de Asignación de Tiempo Global": f"{porcentaje_asignacion_total:.2f}%"
    }

    # Escenario: Subutilización de operarios
    mensaje_final = "Balanceo completado exitosamente."
    if porcentaje_asignacion_total < 95: # Umbral de ejemplo
        mensaje_final += f" NOTA: El tiempo total asignado ({tiempo_total_asignado:.2f} min) es considerablemente menor al disponible. Se podría reducir el número de operarios."

    # --- Construir asignación por operario para el Gantt ---
    asignacion_por_operario = {f'{i+1}': [] for i in range(numero_operarios)}
    for i in range(numero_operarios):
        nombre_col = f'operario_{i+1}'
        rows_con_tiempo = df_asignacion[df_asignacion[nombre_col] > 0]
        for _, r in rows_con_tiempo.iterrows():
             asignacion_por_operario[str(i+1)].append({
                 'minutos_asignados': r[nombre_col],
                 'descripcion': f"{r['codigo_producto']} - {r['OPERACION']}"
             })

    return {
        "mensaje": mensaje_final,
        "df_resultado": df_asignacion,
        "kpis": kpis,
        "asignacion_por_operario": asignacion_por_operario
    }

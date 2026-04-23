# data_loader.py (Versión v3.4 - Con Migración de Esquema)
# CORRECCIÓN: Se añade una lógica de migración para actualizar el esquema de la
# base de datos existente, añadiendo columnas que puedan faltar.

import pandas as pd
import sqlite3
import os
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import unicodedata

# --- CÁLCULO DE RUTA BASE ABSOLUTA PARA LA DB ---\
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data') 

# Rutas de la Base de Datos SQLite
DB_PATH = os.path.join(DATA_DIR, 'textil_scheduler.db')
BOM_MASTER_TABLE = 'BOM_MASTER'
ORDERS_LOG_TABLE = 'ORDERS_LOG'
BALANCED_SCHEDULES_TABLE = 'BALANCED_SCHEDULES'

def _normalize_string(s: str) -> str:
    """
    Función de utilidad para normalizar texto: quita tildes,
    convierte a mayúsculas y reemplaza espacios y guiones.
    """
    if not isinstance(s, str):
        return s
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn')
    return s.upper().strip().replace(' ', '_').replace('-', '_')

def normalizar_columna(nombre):
    raise NotImplementedError


class DataLoader:
    """
    Clase para manejar la persistencia de datos mediante SQLite.
    """
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._initialize_db()
        
    def _connect_db(self):
        return sqlite3.connect(DB_PATH)

    def _run_migrations(self, conn: sqlite3.Connection):
        """
        Revisa el esquema de la base de datos y aplica los cambios necesarios
        (migraciones) para que coincida con el código actual.
        """
        cursor = conn.cursor()
        
        # Migración 1: Asegurarse de que la columna DETALLE_JSON existe en ORDERS_LOG
        cursor.execute(f"PRAGMA table_info({ORDERS_LOG_TABLE})")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'DETALLE_JSON' not in columns:
            print(f"INFO: Ejecutando migración. Añadiendo columna 'DETALLE_JSON' a la tabla {ORDERS_LOG_TABLE}...")
            try:
                cursor.execute(f"ALTER TABLE {ORDERS_LOG_TABLE} ADD COLUMN DETALLE_JSON TEXT")
                print("INFO: Migración completada exitosamente.")
            except Exception as e:
                print(f"ERROR: No se pudo completar la migración de la base de datos: {e}")
        
        # Aquí se podrían añadir futuras migraciones (Ej: "if 'NUEVA_COLUMNA' not in columns...")
        
        conn.commit()

    def _initialize_db(self):
        """Crea las tablas si no existen y ejecuta migraciones de esquema si es necesario."""
        conn = self._connect_db()
        try:
            cursor = conn.cursor()
            
            # Creación de la tabla BOM_MASTER
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {BOM_MASTER_TABLE} (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    REFERENCIA TEXT NOT NULL,
                    DESCRIPCION TEXT,
                    FAMILIA TEXT,
                    PROCESO TEXT,
                    CONSECUTIVO_OPERACION INTEGER,
                    OPERACION TEXT NOT NULL,
                    MAQUINA TEXT,
                    SAM_MINUTOS REAL NOT NULL,
                    UNIQUE(REFERENCIA, PROCESO, CONSECUTIVO_OPERACION)
                )
            """)
            
            # Creación de la tabla ORDERS_LOG
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {ORDERS_LOG_TABLE} (
                    OP_UNIQUE_ID TEXT PRIMARY KEY,
                    FECHA_CREACION TEXT,
                    ESTADO TEXT,
                    CLIENTE TEXT,
                    FECHA_ENTREGA TEXT,
                    PRIORIDAD INTEGER,
                    DETALLE_JSON TEXT
                )
            """)
            
            # Creación de la tabla BALANCED_SCHEDULES
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {BALANCED_SCHEDULES_TABLE} (
                    SCHEDULE_ID TEXT PRIMARY KEY,
                    OP_UNIQUE_ID TEXT,
                    FECHA_BALANCEO TEXT,
                    PARAMETROS_JSON TEXT,
                    RESULTADO_JSON TEXT,
                    FOREIGN KEY(OP_UNIQUE_ID) REFERENCES {ORDERS_LOG_TABLE}(OP_UNIQUE_ID)
                )
            """)
            
            conn.commit()

            # --- Migraciones ---
            cursor.execute(f"PRAGMA table_info({BOM_MASTER_TABLE})")
            bom_columns = [info[1] for info in cursor.fetchall()]
            if 'FAMILIA' not in bom_columns:
                cursor.execute(f"ALTER TABLE {BOM_MASTER_TABLE} ADD COLUMN FAMILIA TEXT")
            if 'PROCESO' not in bom_columns:
                cursor.execute(f"ALTER TABLE {BOM_MASTER_TABLE} ADD COLUMN PROCESO TEXT")

            cursor.execute(f"PRAGMA table_info({ORDERS_LOG_TABLE})")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'DETALLE_JSON' not in columns:
                cursor.execute(f"ALTER TABLE {ORDERS_LOG_TABLE} ADD COLUMN DETALLE_JSON TEXT")
            if 'CLIENTE' not in columns:
                cursor.execute(f"ALTER TABLE {ORDERS_LOG_TABLE} ADD COLUMN CLIENTE TEXT")
            if 'FECHA_ENTREGA' not in columns:
                cursor.execute(f"ALTER TABLE {ORDERS_LOG_TABLE} ADD COLUMN FECHA_ENTREGA TEXT")
            if 'PRIORIDAD' not in columns:
                cursor.execute(f"ALTER TABLE {ORDERS_LOG_TABLE} ADD COLUMN PRIORIDAD INTEGER")
            
            conn.commit()

            # --- ¡AQUÍ ESTÁ LA SOLUCIÓN! ---
            # Ejecutar migraciones después de asegurarse de que las tablas existen
            self._run_migrations(conn)

        finally:
            conn.close()

    

    def normalizar_columna(nombre):
        if not isinstance(nombre, str):
            return nombre
        # Quita tildes y convierte a mayúsculas
        return ''.join(c for c in unicodedata.normalize('NFD', nombre)
                    if unicodedata.category(c) != 'Mn').upper().strip()
    

    
    def cargar_bom_desde_csv(self, file_path: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        try:
            df = pd.read_csv(file_path, sep=';', decimal=',')
            # Crear un mapa de columnas normalizadas
            col_map = {normalizar_columna(col): col for col in df.columns}

            required_cols = ['REFERENCIA', 'DESCRIPCION', 'PROCESO', 'CONSECUTIVO', 'OPERACIÓN', 'MAQUINA', 'SAM-MINUTOS']
            missing_cols = [col for col in required_cols if col not in col_map]
            if missing_cols:
                msg = f"Error: El archivo CSV no contiene las columnas requeridas: {', '.join(missing_cols)}."
                return False, msg, None

            # Renombra las columnas del DataFrame a los nombres estándar requeridos
            df = df.rename(columns={col_map[col]: col for col in required_cols})

            # Filtra filas donde todas las columnas requeridas están vacías
            df = df.dropna(subset=required_cols, how='all')
            df = df[df['SAM-MINUTOS'].notnull()]

            # Convierte SAM-MINUTOS a numérico y elimina filas vacías o no numéricas
            df['SAM-MINUTOS'] = pd.to_numeric(df['SAM-MINUTOS'], errors='coerce')
            df = df[df['SAM-MINUTOS'].notnull()]

            # Opcional: elimina filas donde todas las columnas requeridas están vacías o nulas
            df = df.dropna(subset=required_cols, how='all')

            if df.empty:
                return False, "Error: No hay datos válidos en el archivo CSV.", None

            return True, "Archivo CSV cargado y validado exitosamente.", df

        except FileNotFoundError:
            return False, f"Error: No se encontró el archivo en la ruta: {file_path}", None
        except Exception as e:
            return False, f"Ocurrió un error inesperado al leer el archivo CSV: {e}", None


    def guardar_bom(self, df_bom: pd.DataFrame) -> Tuple[bool, str]:
        """
        Guarda el contenido de un DataFrame del BOM en la base de datos,
        borrando los datos anteriores para evitar duplicados.
        """
        if df_bom is None or df_bom.empty:
            return False, "El DataFrame del BOM está vacío."
        
        df_to_save = df_bom.copy()
        
        # Mapeo de nombres de columnas de la UI/CSV a la Base de Datos
        mapeo_columnas = {
            'CONSECUTIVO': 'CONSECUTIVO_OPERACION',
            'SAM-MINUTOS': 'SAM_MINUTOS',
            'SAM_MINUTOS': 'SAM_MINUTOS' # Por si ya viene con guión bajo
        }
        df_to_save = df_to_save.rename(columns=mapeo_columnas)
        
        # Asegurar que existan PROCESO y CONSECUTIVO_OPERACION si no están
        if 'PROCESO' not in df_to_save.columns:
            df_to_save['PROCESO'] = 'GENERAL'
        if 'CONSECUTIVO_OPERACION' not in df_to_save.columns:
            df_to_save['CONSECUTIVO_OPERACION'] = range(1, len(df_to_save) + 1)

        columnas_db = ['REFERENCIA', 'DESCRIPCION', 'PROCESO', 'CONSECUTIVO_OPERACION', 'OPERACION', 'MAQUINA', 'SAM_MINUTOS']
        
        # Filtrar solo las columnas que existen en el DataFrame y son válidas para la DB
        columnas_finales = [col for col in columnas_db if col in df_to_save.columns]
        df_to_save = df_to_save[columnas_finales]

        conn = self._connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {BOM_MASTER_TABLE}")
            df_to_save.to_sql(BOM_MASTER_TABLE, conn, if_exists='append', index=False)
            conn.commit()
            return True, f"BOM guardado en la base de datos con {len(df_to_save)} registros."
        except Exception as e:
            conn.rollback()
            return False, f"Error al guardar el BOM en la base de datos: {e}"
        finally:
            conn.close()

    def obtener_bom_completo(self) -> Optional[pd.DataFrame]:
        """Obtiene el BOM maestro completo desde la base de datos."""
        try:
            conn = self._connect_db()
            df = pd.read_sql_query(f"SELECT * FROM {BOM_MASTER_TABLE}", conn)
            return df
        except Exception:
            return None
        finally:
            conn.close()

    def obtener_bom_por_referencia(self, referencia: str) -> Optional[pd.DataFrame]:
        """Obtiene las operaciones para una referencia específica con búsqueda robusta."""
        try:
            conn = self._connect_db()
            # Búsqueda exacta primero
            query = f"SELECT * FROM {BOM_MASTER_TABLE} WHERE TRIM(REFERENCIA) = ?"
            df = pd.read_sql_query(query, conn, params=(referencia.strip(),))
            df = df.rename(columns={'CONSECUTIVO_OPERACION': 'CONSECUTIVO', 'SAM_MINUTOS': 'SAM-MINUTOS'})
            return df
        except Exception:
            return None
        finally:
            conn.close()

    def obtener_referencia_nombre_map(self) -> Dict[str, str]:
        """Obtiene un mapa de REFERENCIA -> DESCRIPCION único."""
        try:
            conn = self._connect_db()
            df = pd.read_sql_query(f"SELECT DISTINCT REFERENCIA, DESCRIPCION FROM {BOM_MASTER_TABLE}", conn)
            # Eliminar duplicados de referencia si los hay (tomar la primera descripción)
            df = df.drop_duplicates(subset=['REFERENCIA'])
            return dict(zip(df['REFERENCIA'].astype(str), df['DESCRIPCION'].astype(str)))
        except Exception:
            return {}
        finally:
            conn.close()

    def guardar_orden(self, op_id: str, cliente: str, fecha_entrega: str, prioridad: int, items: List[Dict[str, Any]]) -> None:
        conn = self._connect_db()
        try:
            cursor = conn.cursor()
            detalle = pd.DataFrame(items).to_json(orient='records')
            cursor.execute(
                f"""INSERT OR REPLACE INTO {ORDERS_LOG_TABLE} 
                (OP_UNIQUE_ID, FECHA_CREACION, ESTADO, CLIENTE, FECHA_ENTREGA, PRIORIDAD, DETALLE_JSON) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (op_id, datetime.now().isoformat(), 'Pendiente', cliente, fecha_entrega, prioridad, detalle)
            )
            conn.commit()
        finally:
            conn.close()

    def obtener_orders_log(self) -> pd.DataFrame:
        conn = self._connect_db()
        try:
            simple_query = f"SELECT * FROM {ORDERS_LOG_TABLE} ORDER BY FECHA_CREACION DESC"
            df = pd.read_sql_query(simple_query, conn)
            return df
        finally:
            conn.close()
            
    def guardar_historial_schedule(self, op_unique_id: str, parametros: str, resultado: str) -> None:
        conn = self._connect_db()
        try:
            cursor = conn.cursor()
            import uuid
            schedule_id = f"SCH-{str(uuid.uuid4())[:8]}"
            from datetime import datetime
            
            cursor.execute(
                f"""INSERT INTO {BALANCED_SCHEDULES_TABLE} 
                (SCHEDULE_ID, OP_UNIQUE_ID, FECHA_BALANCEO, PARAMETROS_JSON, RESULTADO_JSON) 
                VALUES (?, ?, ?, ?, ?)""",
                (schedule_id, op_unique_id, datetime.now().isoformat(), parametros, resultado)
            )
            conn.commit()
        finally:
            conn.close()

    def obtener_historial_schedules(self) -> pd.DataFrame:
        conn = self._connect_db()
        try:
            query = f"SELECT * FROM {BALANCED_SCHEDULES_TABLE} ORDER BY FECHA_BALANCEO DESC"
            df = pd.read_sql_query(query, conn)
            return df
        except Exception:
            return pd.DataFrame()
        finally:
            conn.close()

    def obtener_detalle_orden(self, op_id: str) -> Optional[pd.DataFrame]:
        conn = self._connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT DETALLE_JSON FROM {ORDERS_LOG_TABLE} WHERE OP_UNIQUE_ID = ?", (op_id,))
            result = cursor.fetchone()
            if result and result[0]: # Asegurarse que no sea None
                return pd.read_json(result[0])
            return pd.DataFrame() # Devolver DF vacío si no hay detalle
        finally:
            conn.close()

    def actualizar_estado_orden(self, op_id: str, nuevo_estado: str) -> None:
        conn = self._connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE {ORDERS_LOG_TABLE} SET ESTADO = ? WHERE OP_UNIQUE_ID = ?", (nuevo_estado, op_id))
            conn.commit()
        finally:
            conn.close()

    def borrar_orden_por_id(self, op_id: str) -> None:
        conn = self._connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {ORDERS_LOG_TABLE} WHERE OP_UNIQUE_ID = ?", (op_id,))
            conn.commit()
        finally:
            conn.close()

    def exportar_bom_a_csv(self, ruta_archivo: str) -> Tuple[bool, str]:
        """Exporta el BOM completo a un archivo CSV en el formato estándar esperado."""
        try:
            conn = self._connect_db()
            df = pd.read_sql_query(f"SELECT * FROM {BOM_MASTER_TABLE}", conn)
        
            if df.empty:
                return False, "No hay datos BOM para exportar."
            
            df = df.rename(columns={
                'CONSECUTIVO_OPERACION': 'CONSECUTIVO',
                'SAM_MINUTOS': 'SAM-MINUTOS'
            })
        
            columnas_export = ['REFERENCIA', 'DESCRIPCION', 'PROCESO', 'CONSECUTIVO', 'OPERACION', 'MAQUINA', 'SAM-MINUTOS']
            df_export = df[[col for col in columnas_export if col in df.columns]].sort_values(['REFERENCIA', 'PROCESO', 'CONSECUTIVO'])
        
            df_export.to_csv(ruta_archivo, sep=';', index=False, encoding='utf-8')
        
            return True, f"BOM exportado exitosamente a: {ruta_archivo}"
        except Exception as e:
            return False, f"Error al exportar BOM: {str(e)}"

# Instancia única para ser usada en toda la aplicación
data_loader = DataLoader()


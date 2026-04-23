# Arquitectura de Flujo de Información SIPOC - Textiles XYZ Scheduler

Este diagrama modela el flujo completo de la aplicación (versión Python), integrando la metodología SIPOC (Suppliers, Inputs, Process, Outputs, Customers) con un desglose de los **Macroprocesos** y **Microprocesos** a nivel de código y lógica de negocio. También se incluyen las variables y parámetros clave del sistema.

```mermaid
flowchart TD
    %% Definición de Estilos Globales para un diagrama profesional e intuitivo
    classDef supplier fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px,color:#000,font-weight:bold
    classDef input fill:#d5e8d4,stroke:#82b366,stroke-width:2px,color:#000
    classDef variable fill:#e4d7ff,stroke:#9370db,stroke-width:2px,stroke-dasharray: 4 4,color:#000
    classDef macro fill:#f3f3f3,stroke:#666666,stroke-width:2px,color:#000
    classDef process fill:#fff2cc,stroke:#d6b656,stroke-width:2px,color:#000
    classDef output fill:#ffe6cc,stroke:#d79b00,stroke-width:2px,color:#000
    classDef customer fill:#f8cecc,stroke:#b85450,stroke-width:2px,color:#000

    %% ================= S - SUPPLIERS =================
    subgraph Proveedores ["S - Proveedores (Suppliers)"]
        direction TB
        S1(👤 Gerencia / Planificador) ::: supplier
        S2(📄 Archivos Base - Excel/CSV) ::: supplier
        S3(🏢 Área Comercial - Pedidos) ::: supplier
    end

    %% ================= I - INPUTS =================
    subgraph Entradas ["I - Entradas de Información (Inputs) & Parámetros"]
        direction TB
        I1(BOM - Lista de Operaciones) ::: input
        I2(Catálogo de Referencias Textil) ::: input
        I3(Cantidades a Producir) ::: input
        
        %% Variables/Parámetros del Sistema
        V1([🎛️ Variable: Número de Operarios]) ::: variable
        V2([🎛️ Variable: Tiempo de Turno min.]) ::: variable
    end
    
    Proveedores == Alimentan ==> Entradas

    %% ================= P - PROCESS =================
    subgraph Procesos ["P - Macro y Micro Procesos del Sistema (La Aplicación)"]
        direction TB
        
        %% Macroproceso 1
        subgraph MP1 ["Macro 1: Extracción y Limpieza (data_loader)"]
            direction TB
            P1_1(Micro: Cargar Excel a memoria - Pandas DataFrame) ::: process
            P1_2(Micro: Normalizar Nombres y Referencias en Diccionario) ::: process
            P1_1 --> P1_2
        end
        
        %% Macroproceso 2
        subgraph MP2 ["Macro 2: Formulación de Órdenes (ords_view)"]
            direction TB
            P2_1(Micro: Filtrar BOM por Referencia seleccionada) ::: process
            P2_2(Micro: Acumular paquete de trabajo en memoria temporal) ::: process
            P2_1 --> P2_2
        end
        
        %% Macroproceso 3 (El Core)
        subgraph MP3 ["Macro 3: Motor Heurístico de Balanceo (scheduling_engine)"]
            direction TB
            P3_1(Micro: Calcular SAM Total por Referencia) ::: process
            P3_2(Micro: Proyectar Unidades/Hora y Día usando fórmulas) ::: process
            P3_3(Micro: Bucle Secuencial - Asignar Minutos disponibles por Operario) ::: process
            P3_4{Validación: ¿Hay tiempo o operarios suficientes?} ::: process
            
            P3_1 --> P3_2 --> P3_3 --> P3_4
        end
        
        %% Macroproceso 4
        subgraph MP4 ["Macro 4: Análisis Visual y Reportes (gantt & reports)"]
            direction TB
            P4_1(Micro: Calcular métricas % y KPIs Internos) ::: process
            P4_2(Micro: Renderizar Gráfico Gantt y Matplotlib) ::: process
            P4_3(Micro: Exportar DataFrame a Estructura FPDF) ::: process
            
            P4_1 --> P4_2 --> P4_3
        end
        
        MP1 --> MP2 --> MP3 --> MP4
    end

    %% Conexiones hacia Procesos
    Entradas ==>|Inyecta Dataframes| MP1
    V1 -. Condiciona Bucle .-> MP3
    V2 -. Limita Capacidad .-> MP3

    %% ================= O - OUTPUTS =================
    subgraph Salidas ["O - Salidas (Outputs)"]
        direction TB
        O1(📊 DataFrame Final: Asignación Op1...OpN) ::: output
        O2(📉 KPIs: Eficiencia y Tiempos Muertos) ::: output
        O3(🖨️ Archivo Físico PDF / Gantt) ::: output
    end

    Procesos == Procesa y Genera ==> Salidas

    %% ================= C - CUSTOMERS =================
    subgraph Clientes ["C - Clientes (Customers)"]
        direction TB
        C1(🏭 Jefe / Supervisor de Planta) ::: customer
        C2(👷 Operarios Costureros - Ejecutores) ::: customer
        C3(📊 Gerencia DOTEMOS) ::: customer
    end

    Salidas == Visualizado Por ==> Clientes

```

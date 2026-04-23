# BITÁCORA DE PROYECTO: APP TEXTIL SCHEDULER
**Sistema de Programación Desagregada para Producción Textil**

---

## 1. INTRODUCCIÓN Y JUSTIFICACIÓN DEL PROYECTO

### 1.1 El Contexto del Mercado Textil
La industria textil y de confección moderna opera bajo un modelo de **Alta Mezcla y Bajo Volumen (High Mix / Low Volume)** dictado por tendencias de moda rápidas o *Fast Fashion*. El mercado exige tiempos de respuesta (*Lead Times*) cada vez más cortos, lotes más pequeños y alta personalización. Dado que los márgenes de ganancia en confección suelen ser estrechos, la eficiencia operativa en el piso de planta no es un lujo, sino el factor determinante para la supervivencia y rentabilidad de la empresa.

### 1.2 El Problema Operativo (El "Por Qué")
Tradicionalmente, las empresas textiles planifican su piso de planta ( *Shop Floor* ) apoyándose en el conocimiento empírico del supervisor, en hojas de cálculo estáticas, o mediante intuición. Este enfoque manual es incapaz de procesar las múltiples variables dinámicas del entorno de producción de manera simultánea, tales como:
*   La variabilidad de los tiempos estándar (SAM) por cada tipo de producto y operación.
*   La restricción de la capacidad finita de la mano de obra disponible.
*   Las diferentes rutas de proceso de ensamblaje (Ensamble, Terminación, General).

**Consecuencias de la falta de un sistema informático:**
1.  **Altos tiempos de ocio (Muda de Espera):** Desbalanceo en la línea donde operarios quedan sin carga mientras otros están saturados.
2.  **Incumplimiento de fechas de entrega:** Imposibilidad de proyectar con matemáticas exactas si la capacidad instalada puede absorber la carga de trabajo en el tiempo requerido.
3.  **Cuellos de botella impredecibles:** Al cambiar la producción de una referencia a otra, la carga de trabajo fluctúa, generando acumulaciones de inventario en proceso (WIP) descontroladas.

### 1.3 La Solución Propuesta
Nuestra aplicación digitaliza y automatiza este proceso matemático. En lugar de un balanceo a prueba y error, el sistema provee una nivelación rápida, estandarizada y repetible mediante un **algoritmo de Balanceo Heurístico Secuencial**. La herramienta permite responder con exactitud: **¿Qué producir?, ¿Cuánto producir? y ¿Cuándo y con Quién producir?.**

---

## 2. MARCO TEÓRICO Y CONCEPTOS CLAVE

Para comprender el motor de la herramienta, definimos los siguientes principios de Ingeniería de Métodos y Programación de la Producción:

*   **Plan Maestro de Producción (MPS):** Herramienta macro que define las cantidades agregadas a fabricar (ej. semanas o meses). Nuestra app es el paso siguiente al MPS.
*   **Programación Desagregada:** El enfoque central de la APP. Toma una orden específica (cantidades exactas de una Referencia X) y la desglosa al nivel más detallado: tiempo por operación (minutos) asignada a un operario específico.
*   **SAM (Standard Allowed Minute / Minuto Estándar Asignado):** El tiempo que un trabajador calificado necesita para realizar una operación específica a un ritmo normal. En la APP, el SAM es la "moneda" que se divide y reparte de forma equitativa entre la fuerza laboral.
*   **BOM (Bill of Materials / Hoja de Ruta):** A diferencia de la industria metalmecánica (lista de piezas), en confección, el BOM actúa como el 'Routing' o "Secuencia de Operaciones". Define el orden (Unir hombros, Pegar cuello), la máquina requerida y el SAM. Sin el BOM, el algoritmo carece de input para calcular cargas.

### 2.1 Celdas de Manufactura vs. Modelos Tradicionales
*   **Flow Shop (Ej. Ensamblaje Automotriz):** Línea continua, rígida, ideal para volúmenes masivos.
*   **Job Shop (Talleres agrupados por función):** Diferentes departamentos (Solo corte, solo costura plana). Genera mucho traslado y cuellos de botella impredecibles.
*   **Celdas de Manufactura (Modelo de la APP):** Agrupa operarios polivalentes y diversas máquinas en "mini-fábricas" dedicadas a toda la ruta de un lote. La APP asume el modelo de celda, distribuyendo la carga total entre N operarios para que trabajen como un sistema unificado.

### 2.2 Programación por Lotes y Tiempos de Preparación (Setup)
El modelo opera de manera orientada por lotes (Batch). Cambiar hilos, ajustes y adaptar la maquinaria toma tiempo (Setup Time). La programación por lotes en la APP permite agrupar todas las unidades de una misma referencia para procesarlas de corrido en la célula, diluyendo este tiempo improductivo, para luego saltar a la siguiente referencia.

---

## 3. ANÁLISIS DE CUELLOS DE BOTELLA Y FACTORES CRÍTICOS

En ambientes Job Shop o Flow Shop, el cuello de botella es fácilmente visible: es la máquina física más lenta o la estación con una montaña de material esperando.

**¿Cómo maneja y mitiga la APP los Cuellos de Botella?**
La APP emplea el principio de "polivalencia" y "división de tareas líquidas". Si una operación requiere 90 minutos de esfuerzo y el ciclo de un operario es de 60 minutos, la operación en un modelo rígido sería un cuello de botella infranqueable. Sin embargo, nuestro algoritmo heurístico "llena" los 60 minutos del Operario 1, y asigna los 30 minutos restantes al Operario 2. 

**Identificación del Factor Crítico en este software:**
En nuestro modelo, el cuello de botella físico individual se diluye al ser absorbido por la célula de trabajo en conjunto. 
El factor crítico real y que el software alerta ocurre cuando **el Tiempo Total Necesario (SAM acumulado de la demanda) supera el Tiempo Total Disponible (Capacidad Finita de Operarios x Ciclo)**. En ese punto, el sistema entra en un déficit de "Operarios Insuficientes", señalando que la capacidad global de la planta es el límite (Restricción de Sistema).

---

## 4. SIPOC: SISTEMA DE PROGRAMACIÓN DE PRODUCCIÓN

| Elemento | Descripción para la APP |
| :--- | :--- |
| **S (Supplier / Proveedor)** | - Departamento Comercial (Ventas / Demanda)<br>- Ingeniería de Producción (Métodos y Tiempos / Estudios MTM) |
| **I (Input / Entrada)** | - Órdenes de Producción: (Referencia, Cantidad esperada).<br>- Base de datos BOM / Hojas de Ruta: (Operaciones, Secuencia, SAM).<br>- Restricciones de Planta: (# Operarios, Tiempo dispuesto). |
| **P (Process / Procesos)** | 1. Cálculo de Meta Takt Time (Unidades a fabricar por hora).<br>2. Traducción de demanda a carga en minutos (U/H x SAM).<br>3. Ejecución del Algoritmo de Balanceo Heurístico Secuencial.<br>4. Diagramación de Gantt In-Memory.<br>5. Consolidación de Indicadores KPIs. |
| **O (Output / Salida)** | - Plan de Producción Desagregado y balanceado de la orden.<br>- Carga laboral medida en minutos exactos por Operario.<br>- Determinación de la saturación del sistema. |
| **C (Customer / Cliente)** | - Supervisores de Planta.<br>- Lideres de Célula de Manufactura.<br>- Dirección y Gerencia de Producción. |

---

## 5. ARQUITECTURA TÉCNICA Y LÓGICA DEL MOTOR (DIAGRAMA DE FLUJO)

El "cerebro" de la aplicación (Motor Heurístico - [scheduling_engine.py](file:///d:/Documents/APPTextil/proy_textil/TEXTILES_XYZ_SCHEDULER/src/scheduling_engine.py)) funciona bajo los siguientes pasos metodológicos abstractos:

1. **Lectura de Demanda:** Recepción de los datos de la Orden seleccionada (Referencias y Cantidades).
2. **Cruce Referencial:** Validación estricta; el sistema ubica el BOM (SAMs) de la referencia. Si no existe, lanza una "Alerta de Falla de Ingeniería".
3. **Cálculo de Eficacia (Meta Teórica):** 
   `Unidades por Hora a Fabricar = (Cantidad Operarios * Tiempo de Ciclo) / Total SAM de Prenda`
4. **Desagregación Dinámica:** Por cada operación en secuencia:
   `Tiempo Requerido por Operación = SAM de la operación * Unidades por Hora Calculadas`
5. **Bucle de Balanceo Heurístico (Asignación Tipo "Llenado de Contenedores"):**
   - El algoritmo evalúa el *Operario 1* (Contenedor).
   - Ingresa el tiempo de la primera operación disponible al contenedor.
   - Si la operación excede el tiempo libre del operario, la capacidad libre se llena al 100% y el "excedente" de tiempo de la operación rebasa, trasladándose automáticamente a ser asignado al siguiente *Operario (Contenedor 2)*.
   - Si un operario llega a 0 minutos disponibles, el índice avanza estructuralmente al operario consecutivo.
6. **Validación de Factibilidad Constante:** Si la matriz de operaciones tiene remanentes (tiempos sobrantes) y el índice de operarios llega a su límite, se emite una interrupción lógica por "Capacidad Instalada Deficiente".
7. **Motor Visual y Analítico:** Representación visual gráfica tipo Gantt de asignación de minutos y despliegue del Dashboard estadístico global de balanceo.

---

## 6. CONCLUSIÓN

Esta aplicación no es únicamente un modelo de datos estructurado o CRUD, sino una herramienta computacional de **Investigación de Operaciones** aplicada a la industria. Conforma un ecosistema completo para tomar decisiones gerenciales informadas en un modelo desagregado, reemplazando la intuición con un algorítmico matemático puro para balanceo de capacidades en entornos celulares de alta complejidad.

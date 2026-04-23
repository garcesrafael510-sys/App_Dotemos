Textiles XYZ Scheduler v5.0
Sistema de Balanceo y Programación de Producción Textil
Este sistema permite balancear líneas de producción textil, asignando operaciones a operarios de manera eficiente para maximizar la productividad y minimizar los tiempos de entrega. Esta versión introduce una arquitectura modular para facilitar su mantenimiento y escalabilidad.

Características
Gestión de BOM: Carga, visualización y exportación de la base de datos de operaciones.

Creación de Órdenes: Ensamble de "paquetes" de producción seleccionando productos del BOM.

Balanceo de Línea: Asignación de operaciones a operarios mediante un motor heurístico.

Visualización de Resultados: Gráficos de Gantt e indicadores (KPIs) del balanceo.

Interfaz Modular: Navegación intuitiva desde una página de inicio.

Estructura del Proyecto
TEXTILES_XYZ_SCHEDULER/
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt
├── README.md
|
├── gui/                    # Módulos de la Interfaz Gráfica
│   ├── landing_page.py
│   ├── bom_view.py
│   ├── orders_view.py
│   ├── scheduler_view.py
│   ├── reports_view.py
│   └── theme.py
|
├── src/                    # Lógica de negocio y algoritmos
│   ├── data_loader.py
│   ├── scheduling_engine.py
│   ├── gantt_utils.py
│   └── report_generator.py
│
└── data/                   # Datos (CSVs, base de datos SQLite)

Requisitos
Python 3.8 o superior

Dependencias listadas en requirements.txt

Instalación
Clonar el repositorio o descargar los archivos.

Crear la estructura de carpetas como se describe arriba.

Instalar las dependencias:

pip install -r requirements.txt

Uso
Ejecute la aplicación desde la carpeta raíz del proyecto (TEXTILES_XYZ_SCHEDULER):

python main.py

Se abrirá una página de inicio desde donde podrá navegar a los diferentes módulos del sistema.
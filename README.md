# Proyecto 3 – Análisis de la industria cinematográfica con Big Data en AWS

##  Descripción general
Este proyecto construye un **pipeline completo de Big Data** en AWS que integra datos de tres fuentes heterogéneas:

- **MovieLens** (base de datos relacional RDS MariaDB) – calificaciones de usuarios.
- **TMDB API** (fuente URL) – metadatos de películas (presupuesto, recaudación, etc.).
- **Banco Mundial** (archivo simulado en EC2) – PIB per cápita por país.

El flujo incluye ingesta automática a **S3** (zona `Raw/`), procesamiento ETL con **AWS Glue** (y alternativamente con **EMR**), catalogación con **Glue Crawler** y **Hive**, consultas analíticas con **Athena**, **Hive** y **SparkSQL**, análisis con **PySpark**, y finalmente una **aplicación web interactiva con Streamlit** desplegada en EC2 que lee los datos desde S3.

##  Arquitectura del pipeline

```
RDS (MariaDB) ─┐
TMDB API      ─┼──► S3 (Raw/) ──► Glue ETL ──► S3 (Trusted/) ──► Glue Crawler ──► Athena / Hive / SparkSQL
EC2 (GDP)     ─┘                                                              │
                                                                              ▼
                                                                        Streamlit App (EC2)
```

##  Estructura del repositorio

```
.
├── README.md
├── requirements.txt
├── .gitignore
├── scripts/
│   ├── subir_rds_a_s3.py
│   └── obtener_tmdb.py
├── notebooks/
│   ├── 04_procesamiento_raw_to_trusted.ipynb
│   ├── 06_consultas_sparksql.ipynb
│   └── 07_analisis_pyspark.ipynb
├── hive_queries/
│   ├── create_tables_hive.sql
│   └── queries_negocio.sql
└── streamlit_app/
    ├── appv1.py
    ├── appv2.py
    └── appv3.py
```

##  Requisitos previos

- Cuenta de AWS con acceso a S3, RDS, Glue, EMR, EC2, Athena.
- Clave de API de TMDB (registrarse en [themoviedb.org](https://www.themoviedb.org/signup)).
- Archivo `global-bundle.pem` (certificado SSL para RDS) descargado de AWS.
- Instancia EC2 (Ubuntu 24.04 o 26.04) con puertos SSH (22) y Streamlit (8501) abiertos.

##  Instalación y configuración en la EC2

### 1. Conectarse a la EC2
```bash
ssh -i your-key.pem ubuntu@<IP_EC2>
```

### 2. Instalar dependencias del sistema
```bash
sudo apt update
sudo apt install python3-pip mariadb-client-core unzip -y
```

### 3. Crear entorno virtual e instalar librerías Python
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Clonar el repositorio (o copiar los archivos)
```bash
git clone <url-del-repositorio>
cd <repositorio>
```

### 5. Configurar credenciales de AWS
```bash
mkdir -p ~/.aws
nano ~/.aws/credentials
# Pegar las credenciales proporcionadas por el laboratorio (access_key, secret_key, session_token)
```

### 6. Subir datos iniciales a S3 (ejecutar scripts de ingesta)
```bash
# Subir ratings desde RDS
python scripts/subir_rds_a_s3.py

# Obtener metadatos de TMDB y subirlos
python scripts/obtener_tmdb.py

# Subir GDP (archivo ya existente en EC2)
aws s3 cp gdp_data.json s3://mariaolayalab1/Raw/ec2/gdp_data.json
```

##  Procesamiento ETL con AWS Glue

1. En la consola de AWS Glue, crear un nuevo job ETL (script editor).
2. Copiar el contenido del script que se encuentra en la documentación del proyecto (ver `manual para usar glue.md`).
3. Configurar el rol IAM como `LabRole` y ejecutar el job.
4. Verificar que se generen los archivos Parquet en `s3://mariaolayalab1/Trusted/ratings/`, `tmdb/` y `gdp/`.

##  Catalogación con Glue Crawler

1. Crear un Crawler que apunte a `s3://mariaolayalab1/Trusted/`.
2. Ejecutarlo y verificar que se creen las tablas `ratings`, `tmdb`, `gdp` en la base de datos `proyecto3_db`.

##  Consultas SQL con Athena / Hive / SparkSQL

- **Athena**: Ejecutar las queries del archivo `hive_queries/queries_negocio.sql` directamente en la consola de Athena.
- **Hive (EMR)**: Si se despliega un clúster EMR, usar el editor de Hue para ejecutar las mismas queries sobre las tablas externas creadas con `create_tables_hive.sql`.
- **SparkSQL**: Los notebooks `06_consultas_sparksql.ipynb` y `07_analisis_pyspark.ipynb` contienen las consultas y análisis equivalentes.

##  Análisis con PySpark

Los notebooks en la carpeta `notebooks/` muestran el procesamiento ETL alternativo con PySpark en JupyterHub (EMR) y el análisis estadístico completo (correlaciones, ROI, estadísticas descriptivas). Se incluye también el job de Glue del punto 7.

##  Aplicación Streamlit (Punto 8)

La aplicación web se ejecuta en la misma EC2 y lee los datos desde S3 (bucket `mariaolayalab1`). Para lanzarla:

```bash
cd streamlit_app
source ../venv/bin/activate
streamlit run appv3.py --server.port 8501 --server.address 0.0.0.0
```
appv1.py  app inicial con funcionalidades básicas.
appv2.py  app mejorada con lectura local de CSVs (en lugar de S3). 
appv3.py  app mejorada con lectura de S3.

Accede a la app en: `http://<IP_EC2>:8501`

### Funcionalidades de la app (pestañas)

- **Ratings**: distribución de calificaciones, top 10 mejor calificadas, más populares, evolución mensual, boxplot anual.
- **TMDB**: metadatos de películas, gráfico presupuesto vs recaudación (log-log), top 10 recaudación.
- **GDP**: evolución de PIB per cápita por país, top 15 países, tabla pivote últimos 10 años.
- **Correlaciones**: correlaciones budget/revenue vs rating, top 10 ROI, scatter presupuesto vs rating (color/tamaño = ROI), correlación vote_average de TMDB vs rating usuarios.

##  Resultados clave de las preguntas de negocio

1. **Top 10 mejor calificadas** (≥5 ratings) – se listan en la pestaña Ratings.
2. **Distribución de ratings** – la mayoría de los usuarios dan puntuaciones 3, 4 y 5.
3. **Películas más populares** – las que tienen más número de ratings (ej. movieId 356 con 329 ratings).
4. **Evolución temporal** – el rating promedio se mantiene estable alrededor de 3.5 a lo largo de los meses.
5. **Correlación presupuesto vs rating** – coeficiente de Pearson = **0.1432**, indicando relación prácticamente nula.

##  Notas adicionales

- El bucket utilizado es `mariaolayalab1`. Asegúrate de reemplazar el nombre si usas otro.
- Los archivos de `ml-latest-small/` (ratings.csv y movies.csv) se descargan durante la ingesta.
- El certificado SSL `global-bundle.pem` es necesario para conectar a RDS desde el script Python.

##  Autores
- Sofía Acosta – [sacostap](mailto:sacostap@eafit.edu.co)
- Isabela Acosta – [isabela@eafit.edu.co](mailto:isabela@eafit.edu.co)
- María Olaya – [molaya@eafit.edu.co](mailto:molaya@eafit.edu.co)

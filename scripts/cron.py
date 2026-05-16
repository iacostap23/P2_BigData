#!/usr/bin/env python3
"""
cron.py – Automatización de ingesta al Data Lake (RDS, TMDB, GDP)
Ejecutar manualmente o programar con crontab.
"""

import subprocess
import sys
import os
import logging
import time
from datetime import datetime

# Configuración de logs
LOG_FILE = "/home/ubuntu/ingesta.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuración de rutas y parámetros
WORK_DIR = "/home/ubuntu"
RDS_HOST = "db-movies.cbt2des3unwt.us-east-1.rds.amazonaws.com"
RDS_USER = "admin"
RDS_PASSWORD = "71002939"
RDS_DATABASE = "movielens"
BUCKET = "mariaolayalab1"
API_KEY = "044279c983d25fc0b7d831603f31dded"

def run_command(cmd, description):
    """Ejecuta un comando shell y registra resultado."""
    logging.info(f"Ejecutando: {description}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=WORK_DIR)
    if result.returncode == 0:
        logging.info(f"OK: {description}")
        logging.debug(result.stdout)
    else:
        logging.error(f"Fallo en: {description}")
        logging.error(result.stderr)
        raise Exception(f"Error en comando: {description}")
    return result

def descargar_movielens():
    """Descarga y descomprime MovieLens si no existe."""
    if not os.path.exists(f"{WORK_DIR}/ml-latest-small/ratings.csv"):
        logging.info("Descargando MovieLens dataset...")
        run_command("wget -q https://files.grouplens.org/datasets/movielens/ml-latest-small.zip", 
                    "Descargar ml-latest-small.zip")
        run_command("unzip -o ml-latest-small.zip", "Descomprimir dataset")
        logging.info("MovieLens listo.")
    else:
        logging.info("MovieLens ya existe, se omite descarga.")

def crear_tabla_rds():
    """Crea la base de datos y tabla ratings en RDS (si no existen)."""
    logging.info("Conectando a RDS para crear esquema...")
    sql = f"""
    CREATE DATABASE IF NOT EXISTS {RDS_DATABASE};
    USE {RDS_DATABASE};
    CREATE TABLE IF NOT EXISTS ratings (
        userId INT,
        movieId INT,
        rating DECIMAL(2,1),
        timestamp INT
    );
    """
    # Guardar script temporal
    sql_file = f"{WORK_DIR}/tmp_rds.sql"
    with open(sql_file, 'w') as f:
        f.write(sql)
    cmd = f"mysql -h {RDS_HOST} -u {RDS_USER} -p{RDS_PASSWORD} < {sql_file}"
    run_command(cmd, "Crear base de datos y tabla ratings")
    os.remove(sql_file)
    logging.info("Esquema RDS verificado/creado.")

def cargar_ratings_a_rds():
    """Carga ratings.csv a la tabla ratings usando LOAD DATA LOCAL INFILE."""
    csv_path = f"{WORK_DIR}/ml-latest-small/ratings.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"No se encuentra {csv_path}")
    
    logging.info("Cargando ratings a RDS...")
    sql = f"""
    USE {RDS_DATABASE};
    LOAD DATA LOCAL INFILE '{csv_path}'
    INTO TABLE ratings
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\\n'
    IGNORE 1 LINES;
    """
    sql_file = f"{WORK_DIR}/tmp_load.sql"
    with open(sql_file, 'w') as f:
        f.write(sql)
    cmd = f"mysql --local-infile=1 -h {RDS_HOST} -u {RDS_USER} -p{RDS_PASSWORD} < {sql_file}"
    run_command(cmd, "Cargar ratings a RDS")
    os.remove(sql_file)
    logging.info("Ratings cargados exitosamente.")

def subir_ratings_a_s3():
    """Exporta ratings desde RDS y sube CSV a S3 (Raw/rds/ratings.csv)."""
    logging.info("Exportando ratings desde RDS a S3...")
    # Generar CSV en memoria con Python (usando subir_rds_a_s3.py)
    # Alternativa: ejecutar el script existente.
    script_path = f"{WORK_DIR}/subir_rds_a_s3.py"
    if os.path.exists(script_path):
        run_command(f"python3 {script_path}", "Ejecutar subir_rds_a_s3.py")
    else:
        logging.warning("No se encontró subir_rds_a_s3.py, se usará método alternativo.")
        # Método alternativo: usar mysqldump + aws s3 cp? Pero mejor usar el script.
        # Por ahora, mostrar error.
        raise FileNotFoundError("subir_rds_a_s3.py no encontrado")
    logging.info("Ratings subido a S3.")

def obtener_tmdb():
    """Ejecuta script obtener_tmdb.py que descarga metadatos y sube a S3."""
    script_path = f"{WORK_DIR}/obtener_tmdb.py"
    if not os.path.exists(script_path):
        raise FileNotFoundError("obtener_tmdb.py no encontrado")
    run_command(f"python3 {script_path}", "Ejecutar obtener_tmdb.py")
    logging.info("TMDB metadata actualizada en S3.")

def descargar_gdp():
    """Descarga GDP desde API del Banco Mundial y sube a S3."""
    logging.info("Descargando GDP desde API del Banco Mundial...")
    run_command(
        "curl -s -o gdp_data.json 'https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.CD?format=json'",
        "Descargar gdp_data.json"
    )
    run_command(
        f"aws s3 cp gdp_data.json s3://{BUCKET}/Raw/ec2/gdp_data.json",
        "Subir GDP a S3"
    )
    logging.info("GDP actualizado en S3.")

def main():
    logging.info("========== INICIO DE INGESTA AUTOMÁTICA ==========")
    try:
        # 1. Descargar MovieLens
        descargar_movielens()
        
        # 2. Crear tabla en RDS (si no existe)
        crear_tabla_rds()
        
        # 3. Cargar ratings a RDS
        cargar_ratings_a_rds()
        
        # 4. Subir ratings a S3 (desde RDS)
        subir_ratings_a_s3()
        
        # 5. Obtener TMDB y subir a S3
        obtener_tmdb()
        
        # 6. Descargar GDP y subir a S3
        descargar_gdp()
        
        logging.info("========== INGESTA COMPLETADA EXITOSAMENTE ==========")
    except Exception as e:
        logging.error(f"FALLO EN LA INGESTA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
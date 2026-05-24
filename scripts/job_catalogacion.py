import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_date, explode, from_json, schema_of_json, lit
from pyspark.sql.types import IntegerType, DecimalType, StringType, StructType, StructField, ArrayType
from pyspark.sql.functions import expr
import json

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

bucket = "s3://mariaolayalab1"

# ---------- 1. Ratings ----------
print("Leyendo ratings.csv...")
ratings_df = spark.read.option("header", "true").csv(f"{bucket}/Raw/rds/")
ratings_clean = ratings_df.select(
    col("userId").cast(IntegerType()),
    col("movieId").cast(IntegerType()),
    col("rating").cast(DecimalType(2,1)),
    col("timestamp").cast(IntegerType())
).dropna()
ratings_clean.write.mode("overwrite").parquet(f"{bucket}/Trusted/ratings/")
print("Ratings guardado.")

# ---------- 2. TMDB (con países) ----------
print("Leyendo tmdb_metadata.json...")
tmdb_df = spark.read.option("multiline", "true").json(f"{bucket}/Raw/url/tmdb_metadata.json")

# Verificar si las columnas de país existen; si no, crearlas con null
if 'production_country_iso' not in tmdb_df.columns:
    tmdb_df = tmdb_df.withColumn('production_country_iso', lit(None).cast(StringType()))
if 'production_country_name' not in tmdb_df.columns:
    tmdb_df = tmdb_df.withColumn('production_country_name', lit(None).cast(StringType()))

if 'tmdbId' in tmdb_df.columns:
    tmdb_clean = tmdb_df.select(
        col("tmdbId").cast(IntegerType()),
        col("title").cast(StringType()),
        col("budget").cast(IntegerType()),
        col("revenue").cast(IntegerType()),
        col("vote_average").cast(DecimalType(3,1)),
        to_date(col("release_date"), "yyyy-MM-dd").alias("release_date"),
        col("production_country_iso").cast(StringType()),
        col("production_country_name").cast(StringType())
    ).dropna(subset=["tmdbId"])
    tmdb_clean.write.mode("overwrite").parquet(f"{bucket}/Trusted/tmdb/")
    print("TMDB guardado con columnas de país.")
else:
    print("Advertencia: No se encontró la columna 'tmdbId' en el JSON. Se guarda el DataFrame original para depuración.")
    tmdb_df.write.mode("overwrite").json(f"{bucket}/Trusted/tmdb_raw/")

# ---------- 3. GDP (World Bank) ----------
print("Leyendo gdp_data.json...")
gdp_raw = spark.read.text(f"{bucket}/Raw/ec2/gdp_data.json").collect()[0][0]
data = json.loads(gdp_raw)
records = data[1]
from pyspark.sql import Row
rows = []
for record in records:
    rows.append(Row(
        country=record['country']['value'],
        year=int(record['date']),
        gdp_per_capita=record.get('value')
    ))
gdp_df = spark.createDataFrame(rows)
gdp_clean = gdp_df.filter(
    (col("year") >= 2000) & (col("gdp_per_capita").isNotNull())
)
gdp_clean.write.mode("overwrite").parquet(f"{bucket}/Trusted/gdp/")
print("GDP guardado.")

job.commit()
print("✅ Tres fuentes procesadas: ratings, tmdb (con países), gdp")
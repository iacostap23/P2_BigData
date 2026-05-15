
import pymysql
import csv
import boto3
from io import StringIO

rds_host = "db-movies.cbt2des3unwt.us-east-1.rds.amazonaws.com"
rds_user = "admin"
rds_password = "71002939"
rds_database = "movielens"

bucket_name = "mariaolayalab1"
s3_key = "Raw/rds/ratings.csv"

print("Conectando a RDS con SSL...")
conn = pymysql.connect(
    host=rds_host,
    user=rds_user,
    password=rds_password,
    database=rds_database,
    ssl={'ca': 'global-bundle.pem'}   # <-- añadido
)
cursor = conn.cursor()
cursor.execute("SELECT userId, movieId, rating, timestamp FROM ratings")
rows = cursor.fetchall()
cursor.close()
conn.close()

print("Generando CSV en memoria...")
csv_buffer = StringIO()
writer = csv.writer(csv_buffer)
writer.writerow(["userId", "movieId", "rating", "timestamp"])
writer.writerows(rows)

print("Subiendo a S3...")
s3 = boto3.client('s3')
s3.put_object(Bucket=bucket_name, Key=s3_key, Body=csv_buffer.getvalue())
print(f"✅ Listo. Subidos {len(rows)} registros a s3://{bucket_name}/{s3_key}")
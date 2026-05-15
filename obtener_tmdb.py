
import requests
import csv
import json
import time
import boto3

API_KEY = "044279c983d25fc0b7d831603f31dded"
BUCKET = "mariaolayalab1"
S3_KEY = "Raw/url/tmdb_metadata.json"   # o "Raw/api/tmdb_metadata.json" si prefieres

# Leer links.csv para obtener tmdbId
tmdb_ids = []
with open('ml-latest-small/links.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        tmdb_id = row['tmdbId']
        if tmdb_id and tmdb_id.strip() and tmdb_id != '\\N':
            tmdb_ids.append(tmdb_id)
            if len(tmdb_ids) >= 200:
                break

print(f"Obteniendo datos de {len(tmdb_ids)} películas...")

metadatos = []
for i, tmdb_id in enumerate(tmdb_ids):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={API_KEY}&language=en-US"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            metadatos.append({
                'tmdbId': tmdb_id,
                'title': data.get('title'),
                'budget': data.get('budget', 0),
                'revenue': data.get('revenue', 0),
                'vote_average': data.get('vote_average', 0),
                'release_date': data.get('release_date', '')
            })
            print(f"[{i+1}/{len(tmdb_ids)}] OK: {data.get('title')}")
        else:
            print(f"Error {resp.status_code} para {tmdb_id}")
    except Exception as e:
        print(f"Excepción: {e}")
    time.sleep(0.05)

# Guardar localmente
with open('tmdb_metadata.json', 'w') as out:
    json.dump(metadatos, out, indent=2)
print(f"Archivo local guardado con {len(metadatos)} películas.")

# Subir a S3
s3 = boto3.client('s3')
with open('tmdb_metadata.json', 'rb') as f:
    s3.put_object(Bucket=BUCKET, Key=S3_KEY, Body=f)
print(f"✅ Archivo subido a s3://{BUCKET}/{S3_KEY}")
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import boto3

# Configuración de página
st.set_page_config(page_title="Movie Analytics Pro", layout="wide", page_icon="🎬")

# Estilo personalizado
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
        color: #1E3A8A !important;
    }
</style>
""", unsafe_allow_html=True)

# Toggle claro/oscuro
dark_mode = st.toggle("🌙 Modo oscuro", value=False)
if dark_mode:
    st.markdown("""
    <style>
        .stApp {
            background-color: #1e1e1e;
            color: white;
        }
        div[data-testid="metric-container"] {
            background-color: #2d2d2d;
            color: white;
        }
        h1, h2, h3 {
            color: #90caf9 !important;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Movie Analytics Pro")
st.markdown("**Análisis completo de la industria cinematográfica** – Datos: MovieLens, TMDB, Banco Mundial (desde S3)")

# ------------------ CARGA DE DATOS DESDE S3 ------------------
@st.cache_data
def load_data():
    bucket = "mariaolayalab1"
    
    # Leer ratings desde S3
    ratings = pd.read_csv(f"s3://{bucket}/Raw/rds/ratings.csv")
    
    # Leer tmdb desde S3 (ya contiene title)
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key="Raw/url/tmdb_metadata.json")
    tmdb_raw = json.loads(obj['Body'].read().decode('utf-8'))
    tmdb = pd.DataFrame(tmdb_raw) if isinstance(tmdb_raw, list) else pd.DataFrame([tmdb_raw])
    
    # Leer gdp desde S3
    obj_gdp = s3.get_object(Bucket=bucket, Key="Raw/ec2/gdp_data.json")
    gdp_raw = json.loads(obj_gdp['Body'].read().decode('utf-8'))
    gdp_records = gdp_raw[1] if isinstance(gdp_raw, list) and len(gdp_raw) > 1 else []
    gdp_list = []
    for item in gdp_records:
        if isinstance(item, dict) and item.get("value") is not None:
            try:
                year = int(item["date"])
            except:
                year = item["date"]
            gdp_list.append({
                "country": item["country"]["value"],
                "date": year,
                "gdp_per_capita": float(item["value"]) if item["value"] else None
            })
    gdp = pd.DataFrame(gdp_list).dropna(subset=["gdp_per_capita"])
    
    return ratings, tmdb, gdp

# Ahora asignamos solo 3 DataFrames
ratings, tmdb, gdp = load_data()   # <--- CORREGIDO: sin movies


# Convertir a string para merge
ratings['movieId'] = ratings['movieId'].astype(str)
tmdb['tmdbId'] = tmdb['tmdbId'].astype(str)


# Preprocesamiento ratings
ratings['date_dt'] = pd.to_datetime(ratings['timestamp'], unit='s')
ratings['year'] = ratings['date_dt'].dt.year
ratings['month'] = ratings['date_dt'].dt.month
ratings['year_month'] = ratings['date_dt'].dt.to_period('M').astype(str)

# Filtrar ratings para quedarse solo con las películas que existen en tmdb (200 películas)
ratings_filtered = ratings[ratings['movieId'].isin(tmdb['tmdbId'])].copy()

# Calcular avg_ratings (promedio por película) - lo usaremos en tab1 y tab4
# Calcular avg_ratings usando ratings_filtered (solo películas en tmdb)
avg_ratings = ratings_filtered.groupby('movieId').agg(
    avg_rating=('rating', 'mean'),
    num_ratings=('rating', 'count')
).reset_index()
avg_ratings['movieId'] = avg_ratings['movieId'].astype(str)
# Nota: tmdb['tmdbId'] ya lo convertiste antes, no lo repitas

# Métricas generales
total_ratings = len(ratings)
total_movies_rated = ratings['movieId'].nunique()
total_users = ratings['userId'].nunique()
avg_rating_overall = ratings['rating'].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Total Ratings", f"{total_ratings:,}")
col2.metric("🎥 Películas calificadas", total_movies_rated)
col3.metric("👥 Usuarios", total_users)
col4.metric("⭐ Rating promedio", f"{avg_rating_overall:.2f}")

# ------------------ TABS ------------------
tab1, tab2, tab3, tab4 = st.tabs(["⭐ Ratings", "🎥 TMDB", "💰 GDP", "📈 Correlaciones"])

# ========== TAB 1: RATINGS ==========
with tab1:
    st.header("Análisis de calificaciones")
    
    # Distribución
    dist = ratings['rating'].round().value_counts().sort_index().reset_index()
    dist.columns = ['rating', 'count']
    fig = px.bar(dist, x='rating', y='count', title="Distribución de ratings",
                 labels={'rating': 'Estrellas', 'count': 'Frecuencia'},
                 color='count', color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)
    
    # Top 10 mejor calificadas (≥50 ratings)
    st.subheader("🏆 Top 10 mejor calificadas (≥50 ratings)")
    top10 = avg_ratings[avg_ratings['num_ratings'] >= 5].sort_values('avg_rating', ascending=False).head(10)
    # Unir con tmdb para obtener título
    top10 = top10.merge(tmdb, left_on='movieId', right_on='tmdbId', how='inner')
    fig = px.bar(top10, x='avg_rating', y='title', orientation='h',
                 title="Mejor calificadas", color='avg_rating',
                 color_continuous_scale='Viridis', text='avg_rating')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(top10[['title', 'avg_rating', 'num_ratings']], use_container_width=True)
    
    # Más populares
    st.subheader("🔥 Top 10 más populares")
    popular = avg_ratings.sort_values('num_ratings', ascending=False).head(10)
    popular = popular.merge(tmdb, left_on='movieId', right_on='tmdbId', how='inner')
    fig = px.bar(popular, x='num_ratings', y='title', orientation='h',
                 title="Películas con más ratings", color='num_ratings',
                 color_continuous_scale='Oranges')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Evolución mensual
    st.subheader("📈 Evolución del rating promedio por mes")
    monthly = ratings.groupby('year_month')['rating'].mean().reset_index()
    fig = px.line(monthly, x='year_month', y='rating', markers=True,
                  title="Rating promedio mensual", labels={'year_month': 'Mes', 'rating': 'Rating'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Boxplot por año
    st.subheader("📊 Distribución anual")
    fig = px.box(ratings, x='year', y='rating', title="Distribución de ratings por año")
    st.plotly_chart(fig, use_container_width=True)

# ========== TAB 2: TMDB ==========
with tab2:
    st.header("Metadatos TMDB")
    st.dataframe(tmdb, use_container_width=True)
    
    # Budget vs Revenue
    st.subheader("💰 Presupuesto vs Recaudación")
    tmdb_clean = tmdb.dropna(subset=['budget', 'revenue']).copy()
    tmdb_clean = tmdb_clean[tmdb_clean['budget'] > 0]
    if not tmdb_clean.empty:
        fig = px.scatter(tmdb_clean, x='budget', y='revenue', hover_data=['title'],
                         log_x=True, log_y=True,
                         title="Relación presupuesto-recaudación (escala log)",
                         labels={'budget': 'Presupuesto (USD)', 'revenue': 'Recaudación (USD)'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Top recaudación
    st.subheader("🏆 Top 10 recaudación")
    top_rev = tmdb_clean.sort_values('revenue', ascending=False).head(10)
    fig = px.bar(top_rev, x='revenue', y='title', orientation='h',
                 title="Mayor recaudación", color='revenue', color_continuous_scale='Greens')
    st.plotly_chart(fig, use_container_width=True)

# ========== TAB 3: GDP ==========
with tab3:
    st.header("PIB per cápita (Banco Mundial)")
    # Filtro por país
    countries = sorted(gdp['country'].unique())
    selected = st.selectbox("Selecciona un país", countries)
    country_data = gdp[gdp['country'] == selected].sort_values('date')
    fig = px.line(country_data, x='date', y='gdp_per_capita', markers=True,
                  title=f"Evolución del PIB per cápita - {selected}",
                  labels={'date': 'Año', 'gdp_per_capita': 'USD'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Top países en último año
    latest_year = gdp['date'].max()
    top_gdp = gdp[gdp['date'] == latest_year].nlargest(15, 'gdp_per_capita')
    fig = px.bar(top_gdp, x='gdp_per_capita', y='country', orientation='h',
                 title=f"Top 15 países en {latest_year}", color='gdp_per_capita',
                 color_continuous_scale='Teal')
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla pivote últimos 10 años
    st.subheader("Tabla de GDP por país y año (últimos 10 años)")
    recent = gdp[gdp['date'] >= latest_year-10].copy()
    pivot_table = recent.pivot_table(index='country', columns='date', values='gdp_per_capita', aggfunc='first')
    st.dataframe(pivot_table.head(20), use_container_width=True)

# ========== TAB 4: CORRELACIONES Y ROI ==========
with tab4:
    st.header("Correlaciones y retorno de inversión")
    
    # Unir ratings con TMDB (usamos avg_ratings y tmdb)
    merged = tmdb.merge(avg_ratings, left_on='tmdbId', right_on='movieId', how='inner')
    merged = merged[merged['budget'] > 0].dropna(subset=['avg_rating', 'revenue', 'budget'])
    
    if not merged.empty:
        corr_budget = merged['budget'].corr(merged['avg_rating'])
        corr_revenue = merged['revenue'].corr(merged['avg_rating'])
        col_a, col_b = st.columns(2)
        col_a.metric("Correlación Budget vs Rating", f"{corr_budget:.4f}")
        col_b.metric("Correlación Revenue vs Rating", f"{corr_revenue:.4f}")
        
        # ROI
        merged['roi'] = merged['revenue'] / merged['budget']
        top_roi = merged.nlargest(10, 'roi')[['title', 'budget', 'revenue', 'roi']]
        st.subheader("💵 Top 10 ROI (Revenue / Budget)")
        fig = px.bar(top_roi, x='roi', y='title', orientation='h',
                     title="Mayor retorno sobre inversión", color='roi',
                     color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
        
        # Scatter budget vs rating con color ROI
        fig = px.scatter(merged, x='budget', y='avg_rating', size='roi', color='roi',
                         hover_data=['title'], log_x=True,
                         title="Presupuesto vs Rating (tamaño = ROI)",
                         labels={'budget': 'Presupuesto (USD)', 'avg_rating': 'Rating promedio'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay suficientes datos para correlaciones.")
    
    # Correlación vote_average vs rating usuario
    if 'vote_average' in tmdb.columns:
        merged_vote = tmdb.merge(avg_ratings, left_on='tmdbId', right_on='movieId', how='inner')
        merged_vote = merged_vote.dropna(subset=['vote_average', 'avg_rating'])
        if not merged_vote.empty:
            corr_vote = merged_vote['vote_average'].corr(merged_vote['avg_rating'])
            st.metric("Correlación vote_average (TMDB) vs Rating usuarios", f"{corr_vote:.4f}")
            fig = px.scatter(merged_vote, x='vote_average', y='avg_rating', hover_data=['title'],
                             title="TMDB vote_average vs User rating")
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Fuentes: MovieLens (100k ratings), TMDB API, Banco Mundial. App con Streamlit.")

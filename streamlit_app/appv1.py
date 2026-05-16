import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json

st.set_page_config(page_title="Proyecto 3 - Big Data", layout="wide")
st.title("🎬 Dashboard - Análisis de Películas")
st.markdown("Datos desde archivos locales del Datalake")

@st.cache_data
def load_data():
    ratings = pd.read_csv("ml-latest-small/ratings.csv")
    movies  = pd.read_csv("ml-latest-small/movies.csv")

    with open("tmdb_metadata.json") as f:
        tmdb_raw = json.load(f)
    tmdb = pd.DataFrame(tmdb_raw) if isinstance(tmdb_raw, list) else pd.DataFrame([tmdb_raw])

    with open("gdp_data.json") as f:
        gdp_raw = json.load(f)
    gdp_records = gdp_raw[1] if isinstance(gdp_raw, list) and len(gdp_raw) > 1 else []
    gdp_list = []
    for item in gdp_records:
        if isinstance(item, dict) and item.get("value") is not None:
            gdp_list.append({
                "country": item["country"]["value"],
                "date": item["date"],
                "gdp_per_capita": item["value"]
            })
    gdp = pd.DataFrame(gdp_list)

    return ratings, movies, tmdb, gdp

ratings, movies, tmdb, gdp = load_data()

tab1, tab2, tab3 = st.tabs(["⭐ Ratings", "🎥 Películas", "💰 GDP"])

# ══════════════════════════════════════════════════════════
with tab1:
    st.subheader("Distribución de calificaciones")
    dist = ratings["rating"].apply(lambda x: int(x)).value_counts().sort_index()
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots()
        ax.bar(dist.index, dist.values, color="steelblue")
        ax.set_xlabel("Estrellas"); ax.set_ylabel("Cantidad")
        ax.set_title("Distribución de ratings")
        st.pyplot(fig)
    with col2:
        fig2, ax2 = plt.subplots()
        ax2.pie(dist.values, labels=dist.index, autopct="%1.1f%%")
        ax2.set_title("Proporción por estrella")
        st.pyplot(fig2)

    st.subheader("Top 10 películas mejor calificadas (≥ 50 ratings)")
    top = ratings.groupby("movieId").agg(
        avg_rating=("rating", "mean"),
        num_ratings=("rating", "count")
    ).reset_index()
    top = top[top["num_ratings"] >= 50].sort_values("avg_rating", ascending=False).head(10)
    top = top.merge(movies, on="movieId")
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ax3.barh(top["title"], top["avg_rating"], color="coral")
    ax3.set_xlabel("Rating promedio"); ax3.set_xlim(0, 5)
    ax3.set_title("Top 10 películas mejor calificadas")
    ax3.invert_yaxis()
    st.pyplot(fig3)
    st.dataframe(top[["title", "avg_rating", "num_ratings"]], use_container_width=True)

    st.subheader("Ratings por año")
    ratings["year"] = pd.to_datetime(ratings["timestamp"], unit="s").dt.year
    by_year = ratings.groupby("year")["rating"].mean()
    fig4, ax4 = plt.subplots(figsize=(10, 4))
    ax4.plot(by_year.index, by_year.values, marker="o", color="green")
    ax4.set_xlabel("Año"); ax4.set_ylabel("Rating promedio")
    ax4.set_title("Evolución del rating promedio por año")
    st.pyplot(fig4)

# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader("Datos TMDB")
    st.dataframe(tmdb.head(20), use_container_width=True)

    if "budget" in tmdb.columns and "revenue" in tmdb.columns:
        df_rev = tmdb.copy()
        df_rev["revenue"] = pd.to_numeric(df_rev["revenue"], errors="coerce").fillna(0)
        df_rev["budget"]  = pd.to_numeric(df_rev["budget"],  errors="coerce").fillna(0)
        df_rev = df_rev[df_rev["revenue"] > 0].sort_values("revenue", ascending=False).head(10)
        if not df_rev.empty:
            fig5, ax5 = plt.subplots(figsize=(10, 5))
            x = range(len(df_rev))
            ax5.bar([i - 0.2 for i in x], df_rev["budget"] / 1e6,  width=0.4, label="Budget M$",  color="royalblue")
            ax5.bar([i + 0.2 for i in x], df_rev["revenue"] / 1e6, width=0.4, label="Revenue M$", color="orange")
            ax5.set_xticks(list(x))
            labels = df_rev["title"].tolist() if "title" in df_rev.columns else [str(i) for i in df_rev.index]
            ax5.set_xticklabels(labels, rotation=45, ha="right")
            ax5.set_ylabel("Millones USD"); ax5.legend()
            ax5.set_title("Budget vs Revenue Top 10")
            st.pyplot(fig5)

# ══════════════════════════════════════════════════════════
with tab3:
    st.subheader("GDP per cápita por país")
    st.dataframe(gdp.head(20), use_container_width=True)

    if not gdp.empty and "gdp_per_capita" in gdp.columns:
        gdp["gdp_per_capita"] = pd.to_numeric(gdp["gdp_per_capita"], errors="coerce")
        latest = gdp.sort_values("date", ascending=False)
        latest = latest.drop_duplicates(subset="country")
        top_gdp = latest.sort_values("gdp_per_capita", ascending=False).head(15)
        fig6, ax6 = plt.subplots(figsize=(10, 5))
        ax6.barh(top_gdp["country"], top_gdp["gdp_per_capita"], color="teal")
        ax6.set_xlabel("GDP per cápita (USD)")
        ax6.set_title("Top 15 países por GDP per cápita")
        ax6.invert_yaxis()
        st.pyplot(fig6)

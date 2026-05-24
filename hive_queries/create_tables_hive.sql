CREATE DATABASE IF NOT EXISTS isabela_db;
USE isabela_db;

-- Tabla tmdb con los nuevos campos de país
CREATE EXTERNAL TABLE IF NOT EXISTS isabela_db.tmdb (
    tmdbId STRING,
    title STRING,
    budget BIGINT,
    revenue BIGINT,
    vote_average DOUBLE,
    release_date STRING,
    production_country_iso STRING,
    production_country_name STRING
)
STORED AS PARQUET
LOCATION 's3://isabelalake/trusted/tmdb/';

-- Tabla gdp enriquecida con código ISO del país (estructura plana)
CREATE EXTERNAL TABLE IF NOT EXISTS isabela_db.gdp (
    country_name STRING,
    country_iso STRING,
    year INT,
    gdp_per_capita DOUBLE
)
STORED AS PARQUET
LOCATION 's3://isabelalake/trusted/gdp/';

-- Tabla ratings (sin cambios)
CREATE EXTERNAL TABLE IF NOT EXISTS isabela_db.ratings (
    userId STRING,
    movieId STRING,
    rating FLOAT,
    `timestamp` STRING
)
STORED AS PARQUET
LOCATION 's3://isabelalake/trusted/ratings/';
CREATE DATABASE IF NOT EXISTS isabela_db;
USE isabela_db;

CREATE EXTERNAL TABLE IF NOT EXISTS isabela_db.tmdb (
    tmdbId STRING,
    title STRING,
    budget BIGINT,
    revenue BIGINT,
    vote_average DOUBLE,
    release_date STRING
)
STORED AS PARQUET
LOCATION 's3://isabelalake/trusted/tmdb/';

CREATE EXTERNAL TABLE IF NOT EXISTS isabela_db.gdp (
    country MAP<STRING, STRING>,
    countryiso3code STRING,
    `date` STRING,
    `decimal` BIGINT,
    indicator MAP<STRING, STRING>,
    obs_status STRING,
    unit STRING,
    value DOUBLE
)
STORED AS PARQUET
LOCATION 's3://isabelalake/trusted/gdp/';

CREATE EXTERNAL TABLE isabela_db.ratings (
    userId STRING,
    movieId STRING,
    rating FLOAT,
    `timestamp` STRING
)
STORED AS PARQUET
LOCATION 's3://isabelalake/trusted/ratings/';
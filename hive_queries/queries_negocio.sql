--Pregunta 1: Películas con mejor calificación promedio
SELECT 
    r.movieId,
    t.title,
    AVG(r.rating) AS avg_rating,
    COUNT(*) AS num_ratings
FROM ratings r
JOIN tmdb t ON r.movieId = t.tmdbId
GROUP BY r.movieId, t.title
ORDER BY avg_rating DESC
LIMIT 10;


--Pregunta 2: Distribución de calificaciones (frecuencia de cada rating entero)
SELECT 
    ROUND(rating) AS star_rating,
    COUNT(*) AS frequency
FROM ratings
GROUP BY ROUND(rating)
ORDER BY star_rating;

--Pregunta 3: Películas más populares por número de calificaciones recibidas

SELECT 
    movieId,
    COUNT(*) AS num_ratings
FROM ratings
GROUP BY movieId
ORDER BY num_ratings DESC
LIMIT 10;


--Pregunta 4: Evolución temporal del rating promedio por mes/año

SELECT 
    YEAR(FROM_UNIXTIME(CAST(`timestamp` AS BIGINT))) AS year,
    MONTH(FROM_UNIXTIME(CAST(`timestamp` AS BIGINT))) AS month,
    AVG(rating) AS avg_rating,
    COUNT(*) AS total_ratings
FROM ratings
WHERE `timestamp` IS NOT NULL
GROUP BY 
    YEAR(FROM_UNIXTIME(CAST(`timestamp` AS BIGINT))),
    MONTH(FROM_UNIXTIME(CAST(`timestamp` AS BIGINT)))
ORDER BY year, month;

--Pregunta 5: Correlación entre presupuesto y calificación promedio

SELECT 
    t.tmdbId,
    t.title,
    t.budget,
    AVG(r.rating) AS avg_rating,
    COUNT(r.rating) AS num_ratings
FROM tmdb t
JOIN ratings r ON t.tmdbId = r.movieId
WHERE t.budget > 0
GROUP BY t.tmdbId, t.title, t.budget
ORDER BY t.budget DESC
LIMIT 20;

SELECT b.id, b.nombre, b.ciudad, b.presupuesto_signo,
       NVL(b.foto_url, '#APP_IMAGES#bar_default.png') AS imagen
FROM bares b
WHERE :P2_CIUDAD IS NULL OR b.ciudad = :P2_CIUDAD

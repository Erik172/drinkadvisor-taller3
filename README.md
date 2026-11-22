# DrinkAdvisor · Taller 3

Integración de Oracle APEX, FastAPI y MongoDB. Oracle conserva los bares, bebidas y bebedores. MongoDB almacena comentarios y eventos que referencian el ID de un bar de Oracle.

## API

Instala las dependencias con `python -m pip install -r requirements.txt`. Configura las variables de entorno `MONGO_URI`, `MONGO_DB` y `APEX_ORIGINS`. Esta última recibe orígenes separados por comas, sin barras finales (por ejemplo, `https://oracleapex.com`). Ejecuta `python -m uvicorn main:app --host 127.0.0.1 --port 18153`. La documentación interactiva está en `/docs`.

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/` | Comprueba la conexión a MongoDB |
| GET | `/bares/{bar_id}/comentarios` | Lista comentarios del bar |
| POST | `/bares/{bar_id}/comentarios` | Crea un comentario |
| GET | `/bares/{bar_id}/eventos` | Lista eventos del bar |
| POST | `/bares/{bar_id}/eventos` | Crea un evento |

El comentario requiere `texto`. Los campos `autor` y `calificacion` son opcionales. La calificación es un entero de 1 a 5. Cada evento requiere `nombre` y admite atributos variables. La API toma el ID del bar de la ruta y asigna la fecha UTC en ambos POST.

El ejercicio usa peticiones directas del navegador. El autor que envía APEX sirve como etiqueta y CORS controla qué orígenes de navegador pueden leer las respuestas. Para una instalación con datos reales se requiere autenticación del API y autorización de escritura por usuario y bar.

## APEX

La solución se construyó a partir de `DrinkAdvisor_Base_Taller`, aplicación 28560, en Oracle APEX 26.2. Usa el mismo esquema de Oracle. La página 2 conserva las Cards de bares y el filtro de ciudad. La página 3 conserva las bebidas y añade el detalle, los comentarios y los eventos.

Para regenerar la copia importable desde la exportación base del curso:

```powershell
python apex/generar_exportacion.py ruta/a/f28560.sql output/apex/DrinkAdvisor_Taller3.sql https://tu-servicio.onrender.com
```

Importa mediante **App Builder → Import** e instala con un identificador nuevo en el esquema DrinkAdvisor. El valor de `DA_API_BASE` está en **Shared Components → Application Definition Attributes → Substitutions**. Si usas la URL local de prueba, el servicio debe estar ejecutándose en el equipo desde el que se abre APEX.

En la página 3, **Enviar comentario** y **Registrar evento** ejecutan Dynamic Actions. El selector de evento alterna entre los campos de concierto y happy hour.

## Render

Vincula el repositorio remoto que escojas a un Web Service. El archivo `render.yaml` define la instalación, el arranque y el chequeo de salud. En el entorno del servicio, configura `MONGO_URI`, `MONGO_DB` y `APEX_ORIGINS`. Carga la URI directamente como secreto. Después del despliegue, usa el host HTTPS de Render en la sustitución `DA_API_BASE` de APEX.

- [Guía de despliegue de FastAPI en Render](https://render.com/docs/deploy-fastapi)
- [Importación y exportación de Oracle APEX](https://docs.oracle.com/en/database/oracle/apex/26.2/apxdc/exporting-and-importing-applications.html)
- [Operaciones CRUD con PyMongo](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/)

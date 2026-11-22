"""API de comentarios y eventos de DrinkAdvisor."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pymongo import DESCENDING, MongoClient
from pymongo.errors import PyMongoError

BarId = Annotated[int, Path(gt=0)]
Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class Comentario(BaseModel):
    texto: Texto
    autor: Nombre | None = None
    calificacion: Annotated[int, Field(strict=True, ge=1, le=5)] | None = None


class Evento(BaseModel):
    model_config = ConfigDict(extra="allow")

    nombre: Nombre


@asynccontextmanager
async def abrir_mongo(app: FastAPI):
    uri = os.environ["MONGO_URI"]
    nombre_bd = os.environ["MONGO_DB"]
    with MongoClient(uri, serverSelectionTimeoutMS=5000) as client:
        app.state.db = client[nombre_bd]
        yield


app = FastAPI(title="DrinkAdvisor API", lifespan=abrir_mongo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("APEX_ORIGINS", "").split(",") if origin.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(PyMongoError)
async def error_mongo(request: Request, error: PyMongoError):
    return JSONResponse(status_code=503, content={"detail": "Base documental no disponible."})


def listar_documentos(coleccion, bar_id):
    return [
        {**documento, "_id": str(documento["_id"])}
        for documento in coleccion.find({"bar_id": bar_id}).sort("_id", DESCENDING)
    ]


def fecha_actual():
    return datetime.now(timezone.utc).isoformat()


@app.get("/")
def inicio(request: Request):
    request.app.state.db.command("ping")
    return {"estado": "API funcionando correctamente"}


@app.get("/bares/{bar_id}/comentarios")
def get_comentarios(bar_id: BarId, request: Request):
    return listar_documentos(request.app.state.db.comentarios_bares, bar_id)


@app.post("/bares/{bar_id}/comentarios", status_code=201)
def post_comentario(bar_id: BarId, datos: Comentario, request: Request):
    documento = datos.model_dump(exclude_none=True)
    documento.update(bar_id=bar_id, fecha=fecha_actual())
    resultado = request.app.state.db.comentarios_bares.insert_one(documento)
    return {"mensaje": "Comentario guardado", "_id": str(resultado.inserted_id)}


@app.get("/bares/{bar_id}/eventos")
def get_eventos(bar_id: BarId, request: Request):
    return listar_documentos(request.app.state.db.eventos, bar_id)


@app.post("/bares/{bar_id}/eventos", status_code=201)
def post_evento(bar_id: BarId, datos: Evento, request: Request):
    documento = {"nombre": datos.nombre}
    for campo, valor in datos.model_extra.items():
        if campo in {"_id", "bar_id", "fecha_creacion"}:
            continue
        if "." in campo or campo.startswith("$"):
            raise HTTPException(422, "Nombre de campo de evento inválido.")
        if isinstance(valor, str):
            valor = valor.strip()
        if valor is not None and valor != "":
            documento[campo] = valor
    documento.update(bar_id=bar_id, fecha_creacion=fecha_actual())
    resultado = request.app.state.db.eventos.insert_one(documento)
    return {"mensaje": "Evento guardado", "_id": str(resultado.inserted_id)}

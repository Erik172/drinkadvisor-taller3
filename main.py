"""Punto de entrada compatible con uvicorn main:app."""

from importlib import import_module

app = import_module("mongo-api").app

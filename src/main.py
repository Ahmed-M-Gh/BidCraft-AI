from fastapi import FastAPI
from .routes import base_route, reader_router

app = FastAPI()

# Endpoints
app.include_router(base_route)
app.include_router(reader_router)
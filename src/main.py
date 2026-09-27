from fastapi import FastAPI
from .routes import base_route

app = FastAPI()

# Endpoints
app.include_router(base_route)

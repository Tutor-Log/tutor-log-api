import os
from fastapi import FastAPI
from api.routes import base_router

app = FastAPI()

app.include_router(base_router)

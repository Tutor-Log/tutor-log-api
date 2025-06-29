import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers.base import base_router
from database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="Tutor Log API",
    description="A FastAPI application for managing tutoring sessions, pupils, and payments",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(base_router)

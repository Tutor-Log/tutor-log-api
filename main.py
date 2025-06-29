import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import base, user, pupil, group, event, payment
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
origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
print(f"Allowed origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(base)
app.include_router(user)
app.include_router(pupil)
app.include_router(group)
app.include_router(event)
app.include_router(payment)

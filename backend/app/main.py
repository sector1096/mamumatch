from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_partidas_jobs import jobs_router, router as partidas_router
from app.db.init_db import ensure_pipeline_jobs_table


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_pipeline_jobs_table()
    yield


app = FastAPI(title="MamuMatch API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(partidas_router)
app.include_router(jobs_router)
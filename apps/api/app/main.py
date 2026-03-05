from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.catalog import router as catalog_router
from app.api.routes.evals import router as evals_router
from app.api.routes.governance import router as governance_router
from app.api.routes.imports import router as imports_router
from app.api.routes.runs import router as runs_router
from app.config.settings import settings
from app.repositories.bootstrap import bootstrap_database

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Deterministic NSCLC evidence triage API with governance and evaluation scaffolding.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router)
app.include_router(catalog_router)
app.include_router(evals_router)
app.include_router(governance_router)
app.include_router(imports_router)


@app.on_event("startup")
def startup_event():
    bootstrap_database()


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "ok",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


@app.get("/health")
def healthcheck():
    return {"status": "ok", "service": settings.app_name, "databaseUrl": settings.database_url}

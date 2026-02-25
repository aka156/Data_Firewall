from fastapi import FastAPI
from data_quality_firewall.api.routes.health import router as health_router
from data_quality_firewall.api.routes.upload import router as upload_router

from data_quality_firewall.db.database import engine, Base
from data_quality_firewall.models import run  # IMPORTANT: import module, not class


def create_app() -> FastAPI:
    app = FastAPI(title="Data Quality Firewall", version="0.1.0")

    Base.metadata.create_all(bind=engine)

    app.include_router(health_router)
    app.include_router(upload_router)

    return app


app = create_app()

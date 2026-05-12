from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import engine, Base
from app.models import audit_log  # audit_log tablosunu oluştur
from app.routes.records import router as records_router
from app.routes.dashboard import router as dashboard_router
from app.routes.audit import router as audit_router
from app.scheduler.tasks import check_expired_records

# Tablolar yoksa oluştur
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_expired_records,
        trigger="interval",
        hours=1,
        id="expire_check",
    )
    scheduler.start()
    print("[Zamanlayıcı] Başlatıldı — her 24 saatte bir çalışacak.")
    check_expired_records()
    yield
    scheduler.shutdown()
    print("[Zamanlayıcı] Durduruldu.")


app = FastAPI(
    title="Silge API",
    description="Veri İmha ve Yaşam Döngüsü Takip Sistemi",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS — frontend'in backend'e erişmesine izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite'nin portu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(records_router)
app.include_router(dashboard_router)
app.include_router(audit_router)


@app.get("/")
def root():
    return {"message": "Silge API çalışıyor.", "docs": "/docs"}

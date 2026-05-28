from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
import models  # noqa: F401 — registers models before create_all
from routers import auth, organizations, bulletins, sections, entries, logs, archives


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Veritabanı tabloları hazır")
    except Exception as e:
        print(f"⚠ Veritabanına bağlanılamadı: {e}")
    yield


app = FastAPI(
    title="SPK Haftalık Bülten API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,          prefix="/auth",          tags=["Kimlik Doğrulama"])
app.include_router(organizations.router, prefix="/organizations", tags=["Organizasyon"])
app.include_router(bulletins.router,     prefix="/bulletins",     tags=["Bültenler"])
app.include_router(sections.router,      prefix="/sections",      tags=["Bölümler"])
app.include_router(entries.router,       prefix="/entries",       tags=["Kayıtlar"])
app.include_router(logs.router,          prefix="/logs",          tags=["İşlem Kayıtları"])
app.include_router(archives.router,      prefix="/archives",      tags=["Arşiv"])


@app.get("/health", tags=["Sistem"])
def health():
    return {"status": "ok", "version": "2.0.0"}

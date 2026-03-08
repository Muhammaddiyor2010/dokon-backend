from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api import api_router
from app.core.config import get_settings, parse_cors_origins, parse_trusted_hosts
from app.core.database import Base, SessionLocal, engine
from app.services.seed import seed_all

settings = get_settings()


def _build_cors_origins() -> list[str]:
    origins = set(parse_cors_origins(settings.cors_origins))
    if settings.frontend_url.strip():
        origins.add(settings.frontend_url.rstrip("/"))

    if not settings.is_production:
        origins.update(
            {
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            }
        )

    return sorted(origin for origin in origins if origin)


def _build_allowed_hosts() -> list[str]:
    return parse_trusted_hosts(settings.trusted_hosts)


def _health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


ALLOW_ORIGIN_REGEX = r"https?://(localhost|127\.0\.0\.1)(:\d+)?$"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_all(db, include_catalog=settings.seed_catalog_on_startup)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url=f"{settings.api_prefix}/openapi.json" if settings.docs_enabled else None,
)

allowed_hosts = _build_allowed_hosts()
if allowed_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_cors_origins(),
    allow_origin_regex=None if settings.is_production else ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return _health_payload()


@app.get("/health")
def health_check():
    return _health_payload()

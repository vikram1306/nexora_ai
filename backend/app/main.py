import time
import uuid

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import auth, health, ingest, query, sentinel
from app.core.config import settings
from app.core.database import Base, engine
from app.core.limiter import limiter
from app.core.logging_config import clear_request_context, get_logger, set_request_context, setup_logging

# 1. Initialize Structured Logging
setup_logging(log_level=settings.LOG_LEVEL, structured=settings.LOG_STRUCTURED)
logger = get_logger("nexora.gateway")

# 2. Optional Sentry Error Tracking Integration
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            release=f"nexora-ai@{settings.VERSION}",
            traces_sample_rate=0.2,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()]
        )
        logger.info(f"Sentry APM initialized in environment: {settings.ENVIRONMENT}")
    except Exception as e:
        logger.warning(f"Could not initialize Sentry: {e}")

# Initialize SQLAlchemy tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Enterprise Intelligence AI Operating System platform"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 3. Request Correlation ID & Access Logging Middleware
@app.middleware("http")
async def correlation_and_logging_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id
    set_request_context(request_id=req_id)

    start_time = time.perf_counter()
    try:
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = req_id

        # Don't log spammy health probes at info level
        if "/health" not in request.url.path:
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )
        return response
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.exception(
            f"Unhandled exception during {request.method} {request.url.path}: {exc}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": 500,
                "duration_ms": duration_ms
            }
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal Server Error",
                "request_id": req_id,
                "error": str(exc) if settings.ENVIRONMENT != "production" else "Internal server error"
            },
            headers={"X-Request-ID": req_id}
        )
    finally:
        clear_request_context()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)  # Root /health, /health/liveness, /health/readiness
app.include_router(health.router, prefix=settings.API_V1_STR) # /api/v1/health
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(ingest.router, prefix=settings.API_V1_STR)
app.include_router(query.router, prefix=settings.API_V1_STR)
app.include_router(sentinel.router, prefix=settings.API_V1_STR)

@app.get("/")
def root_check():
    return {
        "platform": settings.PROJECT_NAME,
        "tagline": "Enterprise Intelligence. Autonomous Decisions.",
        "status": "online",
        "version": settings.VERSION
    }

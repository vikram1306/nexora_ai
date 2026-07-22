from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1 import auth, ingest, query, sentinel

# Initialize SQLAlchemy tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Enterprise Intelligence AI Operating System platform"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
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

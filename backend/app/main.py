from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import SmartDocException
from app.db.database import engine, Base
from app.api.v1 import auth, documents, analysis, chat, system

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables & apply lightweight auto-migrations
    logger.info("Initializing SmartDoc database connection and schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Ensure missing columns in SQLite table document_analyses are added dynamically
        try:
            await conn.execute(text("ALTER TABLE document_analyses ADD COLUMN is_fallback BOOLEAN DEFAULT 0"))
        except Exception:
            pass
            
        try:
            await conn.execute(text("ALTER TABLE document_analyses ADD COLUMN fallback_notice TEXT"))
        except Exception:
            pass

    yield
    logger.info("Shutting down SmartDoc API engine.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Exception handlers
@app.exception_handler(SmartDocException)
async def smartdoc_exception_handler(request: Request, exc: SmartDocException) -> JSONResponse:
    logger.warning(f"Domain Exception [{exc.error_code}]: {exc.message} (Path: {request.url.path})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled Exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred while processing your request.",
            "details": {}
        }
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
app.include_router(analysis.router, prefix=f"{settings.API_V1_STR}/analysis", tags=["Analysis"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(system.router, prefix=f"{settings.API_V1_STR}/system", tags=["System"])

@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "llm_provider": settings.LLM_PROVIDER
    }

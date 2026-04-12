from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from app.api import documents, reports, auth, admin
from app.core.exceptions import AlethianException, alethian_exception_handler, validation_exception_handler
from app.core.logging import setup_logging

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.rate_limit import limiter

# Activate structured logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.models import Base
    from app.db.session import engine
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Alethian API", version="2.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(AlethianException, alethian_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

@app.get("/")
def read_root():
    return {"message": "Alethian API is running"}

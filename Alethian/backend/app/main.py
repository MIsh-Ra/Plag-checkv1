from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import documents
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    from app.db.models import Base
    from app.db.session import engine
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Alethian API", version="1.0", lifespan=lifespan)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])

@app.get("/")
def read_root():
    return {"message": "Alethian API is running"}

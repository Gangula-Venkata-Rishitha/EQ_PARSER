"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes_parse import router as parse_router
from .routes_query import router as query_router
from .routes_convert import router as convert_router
from .routes_chat import router as chat_router

app = FastAPI(
    title="Equation Parser API",
    description="API for parsing PDFs and extracting equations, logic formulas, and SRS requirements",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(parse_router)
app.include_router(query_router)
app.include_router(convert_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Equation Parser API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

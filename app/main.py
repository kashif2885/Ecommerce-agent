import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Global singletons initialised during startup
graph = None
vectorstore = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph, vectorstore

    from app.config import settings
    from app.rag.ingestion import load_or_create_vectorstore
    from app.agent.graph import build_graph

    print("Initialising RAG vectorstore…")
    vectorstore = load_or_create_vectorstore(
        pdf_path=settings.pdf_path,
        persist_dir=settings.chroma_persist_dir,
        embedding_model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )

    print("Building LangGraph agent…")
    graph = build_graph(
        vectorstore=vectorstore,
        model_name=settings.model_name,
        api_key=settings.openai_api_key,
    )

    print("Agent ready ✓")
    yield

    print("Shutting down…")


app = FastAPI(title="AI Chat Agent – FeelixAI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import chat  # noqa: E402

app.include_router(chat.router, prefix="/api")

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")


@app.get("/products", include_in_schema=False)
async def products_page():
    return FileResponse(os.path.join(static_dir, "products.html"))


# Serve the single-page frontend from /static  (must be last — catches everything)
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

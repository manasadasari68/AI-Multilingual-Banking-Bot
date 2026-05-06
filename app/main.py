import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.chatbot import answer_question, build_chatbot
from app.customer_data import load_customers
from app.rag import build_vector_store, load_vector_store, save_vector_store, summarize_knowledge_base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("banking_bot")

app_state: Dict[str, object] = {
    "vector_store": None,
    "chatbot": None,
    "sessions": {},
    "customers": [],
    "knowledge_files": [],
    "chunk_count": 0,
}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    preferred_language: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    language: str
    language_code: str
    translated_query: str
    response: str
    response_in_english: str
    sources: List[Dict[str, str]]
    history: List[Dict[str, str]]


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting multilingual banking support bot.")

    vector_store = load_vector_store()
    if vector_store is None:
        logger.info("No FAISS index found. Building a fresh knowledge base from PDFs.")
        vector_store, chunk_count, file_names = build_vector_store()
        save_vector_store(vector_store)
    else:
        logger.info("Existing FAISS index loaded successfully.")
        chunk_count, file_names = summarize_knowledge_base()

    app_state["vector_store"] = vector_store
    app_state["chatbot"] = build_chatbot(vector_store)
    app_state["customers"] = load_customers()
    app_state["knowledge_files"] = file_names
    app_state["chunk_count"] = chunk_count

    yield


app = FastAPI(
    title="Multilingual Banking Support Bot",
    description="FastAPI backend for a multilingual banking assistant using OpenRouter, LangChain, and FAISS.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Multilingual Banking Support Bot",
        "knowledge_files": app_state["knowledge_files"],
        "chunk_count": app_state["chunk_count"],
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if app_state["chatbot"] is None:
        raise HTTPException(status_code=503, detail="Chatbot is still starting up.")

    session_id = request.session_id or str(uuid4())
    history = app_state["sessions"].get(session_id, [])

    try:
        response = answer_question(
            app_state["chatbot"],
            request.message,
            history=history,
            preferred_language=request.preferred_language,
            customers=app_state["customers"],
        )
        app_state["sessions"][session_id] = response["history"]
        response["session_id"] = session_id
        return response
    except Exception as exc:
        logger.exception("Failed to process chat request")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {exc}") from exc


@app.post("/reindex")
def reindex():
    try:
        vector_store, chunk_count, file_names = build_vector_store()
        save_vector_store(vector_store)
        app_state["vector_store"] = vector_store
        app_state["chatbot"] = build_chatbot(vector_store)
        app_state["customers"] = load_customers()
        app_state["knowledge_files"] = file_names
        app_state["chunk_count"] = chunk_count
        app_state["sessions"] = {}
        return {
            "status": "reindexed",
            "knowledge_files": file_names,
            "chunk_count": chunk_count,
        }
    except Exception as exc:
        logger.exception("Knowledge base reindex failed")
        raise HTTPException(status_code=500, detail=f"Reindex failed: {exc}") from exc

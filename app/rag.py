import logging
from pathlib import Path
from typing import List, Tuple

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_DIR,
    EMBEDDING_MODEL,
    PDF_GLOB_PATTERNS,
    VECTOR_INDEX_NAME,
    VECTOR_STORE_DIR,
)

logger = logging.getLogger(__name__)


def _embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def discover_pdf_paths() -> List[Path]:
    pdf_paths: List[Path] = []
    for pattern in PDF_GLOB_PATTERNS:
        pdf_paths.extend(sorted(DATA_DIR.glob(pattern)))
    unique_paths = []
    seen = set()
    for path in pdf_paths:
        if path.is_file() and path not in seen:
            unique_paths.append(path)
            seen.add(path)
    return unique_paths


def load_documents(pdf_paths: List[Path]) -> List[Document]:
    documents: List[Document] = []
    for path in pdf_paths:
        logger.info("Loading PDF: %s", path.name)
        loader = PyPDFLoader(str(path))
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = path.name
        documents.extend(docs)
    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    return splitter.split_documents(documents)


def build_vector_store() -> Tuple[FAISS, int, List[str]]:
    pdf_paths = discover_pdf_paths()
    if not pdf_paths:
        raise RuntimeError("No PDF documents found in the data directory.")

    documents = load_documents(pdf_paths)
    if not documents:
        raise RuntimeError("PDF files were found, but no readable content could be extracted.")

    split_docs = split_documents(documents)
    logger.info("Creating FAISS index from %s chunks.", len(split_docs))
    store = FAISS.from_documents(split_docs, _embedding_model())
    return store, len(split_docs), [path.name for path in pdf_paths]


def summarize_knowledge_base() -> Tuple[int, List[str]]:
    pdf_paths = discover_pdf_paths()
    if not pdf_paths:
        return 0, []

    documents = load_documents(pdf_paths)
    split_docs = split_documents(documents) if documents else []
    return len(split_docs), [path.name for path in pdf_paths]


def save_vector_store(store: FAISS) -> Path:
    VECTOR_STORE_DIR.mkdir(exist_ok=True)
    store.save_local(str(VECTOR_STORE_DIR), index_name=VECTOR_INDEX_NAME)
    return VECTOR_STORE_DIR


def load_vector_store() -> FAISS | None:
    index_path = VECTOR_STORE_DIR / f"{VECTOR_INDEX_NAME}.faiss"
    docstore_path = VECTOR_STORE_DIR / f"{VECTOR_INDEX_NAME}.pkl"
    if not index_path.exists() or not docstore_path.exists():
        return None

    logger.info("Loading FAISS index from %s", VECTOR_STORE_DIR)
    return FAISS.load_local(
        str(VECTOR_STORE_DIR),
        _embedding_model(),
        index_name=VECTOR_INDEX_NAME,
        allow_dangerous_deserialization=True,
    )

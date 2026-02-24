"""
RAG ingestion: extract text from a PDF with pdfplumber, chunk it, embed with
text-embedding-3-large, and persist to ChromaDB.

On subsequent starts the existing persisted collection is reloaded, so
re-embedding only happens once.
"""
import os

import pdfplumber
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_text_from_pdf(pdf_path: str) -> str:
    """Return the full text of a PDF, page by page, using pdfplumber."""
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append(f"[Page {i + 1}]\n{text.strip()}")
    return "\n\n".join(pages)


def load_or_create_vectorstore(
    pdf_path: str,
    persist_dir: str,
    embedding_model: str,
    api_key: str,
) -> Chroma:
    """Return an existing ChromaDB vectorstore or create one by ingesting the PDF."""
    embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=api_key)

    # If the persist directory already has data, load it
    if os.path.isdir(persist_dir) and any(os.scandir(persist_dir)):
        print(f"[RAG] Loading existing vectorstore from '{persist_dir}'")
        return Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    print(f"[RAG] Ingesting PDF '{pdf_path}' …")
    raw_text = extract_text_from_pdf(pdf_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=80,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    docs: list[Document] = splitter.create_documents(
        [raw_text],
        metadatas=[{"source": os.path.basename(pdf_path)}],
    )

    print(f"[RAG] Created {len(docs)} chunks – embedding with '{embedding_model}' …")
    vectorstore = Chroma.from_documents(
        docs,
        embeddings,
        persist_directory=persist_dir,
    )
    print(f"[RAG] Vectorstore persisted to '{persist_dir}' ✓")
    return vectorstore

from pathlib import Path
from typing import List, TypedDict
from datetime import datetime
import json
import os
import re

from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document as DocxDocument

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import (
    Base,
    engine,
    get_db,
)
from .models import Conversation, Document, Message

import chromadb
from sentence_transformers import SentenceTransformer

from langchain_groq import ChatGroq
from langgraph.graph import (
    StateGraph,
    END,
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

if not GROQ_API_KEY:
    print(
        "WARNING: GROQ_API_KEY is not configured."
    )


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Enterprise AI Workspace API",
    version="1.0.0",
)


# =========================================================
# DATABASE
# =========================================================

@app.on_event("startup")
def initialize_database():

    Base.metadata.create_all(
        bind=engine
    )


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DIRECTORIES
# =========================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent.parent
)

UPLOAD_DIR = (
    BASE_DIR / "uploads"
)

CHROMA_DIR = (
    BASE_DIR / "chroma_db"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CHROMA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# CONFIGURATION
# =========================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

RETRIEVAL_CANDIDATES = 10
MAX_CONTEXT_CHUNKS = 5
MAX_CHUNKS_PER_DOCUMENT = 2

DOCUMENT_QUERY_MAX_CHUNKS = 20
SUMMARY_MAX_CHUNKS = 20

MAX_CONTEXT_CHARACTERS = 18000


# =========================================================
# EMBEDDING MODEL
# =========================================================

print(
    "Loading embedding model..."
)

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print(
    "Embedding model loaded."
)


# =========================================================
# CHROMADB
# =========================================================

print(
    "Initializing ChromaDB..."
)

chroma_client = chromadb.PersistentClient(
    path=str(
        CHROMA_DIR
    )
)

documents_collection = (
    chroma_client.get_or_create_collection(
        name="enterprise_documents",
        metadata={
            "description": (
                "Enterprise AI Workspace document "
                "knowledge base"
            )
        },
    )
)

print(
    "ChromaDB initialized."
)


# =========================================================
# GROQ
# =========================================================

llm = None

if GROQ_API_KEY:

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.1,
    )

    print(
        f"Groq LLM initialized: "
        f"{GROQ_MODEL}"
    )


# =========================================================
# REQUEST MODELS
# =========================================================

class SearchRequest(BaseModel):

    query: str

    top_k: int = 5


class ChatRequest(BaseModel):

    message: str


class DriveSearchRequest(BaseModel):

    query: str

    max_files: int = 5


class ConversationCreateRequest(BaseModel):

    conversation_id: str | None = None
    title: str = "New Chat"


class ConversationMessageRequest(BaseModel):

    role: str
    content: str
    sources: list[str] | None = None
    agent_workflow: dict | list | str | None = None
    action_result: dict | list | str | None = None


# =========================================================
# CONVERSATION HELPERS
# =========================================================

def serialize_conversation_metadata(value):

    if value is None:
        return None

    if isinstance(value, str):
        return value

    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def deserialize_conversation_metadata(value):

    if value is None or value == "":
        return None

    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return value


def conversation_to_dict(conversation: Conversation):

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
    }


def message_to_dict(message: Message):

    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "sources": deserialize_conversation_metadata(message.sources) or [],
        "agent_workflow": deserialize_conversation_metadata(message.agent_workflow),
        "action_result": deserialize_conversation_metadata(message.action_result),
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


# =========================================================
# CONVERSATIONS
# =========================================================

@app.post("/conversations")
def create_conversation(
    request: ConversationCreateRequest,
    db: Session = Depends(get_db),
):

    conversation_id = (request.conversation_id or "").strip()
    title = request.title.strip() or "New Chat"

    if conversation_id:
        existing = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if existing:
            return conversation_to_dict(existing)

    else:
        import uuid
        conversation_id = str(uuid.uuid4())

    conversation = Conversation(
        id=conversation_id,
        title=title[:255],
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation_to_dict(conversation)


@app.get("/conversations")
def list_conversations(
    limit: int = 50,
    db: Session = Depends(get_db),
):

    limit = max(1, min(limit, 100))

    conversations = (
        db.query(Conversation)
        .order_by(
            Conversation.updated_at.desc(),
            Conversation.created_at.desc(),
        )
        .limit(limit)
        .all()
    )

    return {
        "conversations": [
            conversation_to_dict(conversation)
            for conversation in conversations
        ],
        "count": len(conversations),
    }


@app.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
):

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )

    return {
        **conversation_to_dict(conversation),
        "messages": [message_to_dict(message) for message in messages],
    }


@app.post("/conversations/{conversation_id}/messages")
def add_conversation_message(
    conversation_id: str,
    request: ConversationMessageRequest,
    db: Session = Depends(get_db),
):

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    role = request.role.strip().lower()
    content = request.content.strip()

    if role not in {"user", "assistant", "system"}:
        raise HTTPException(
            status_code=400,
            detail="Message role must be user, assistant, or system.",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Message content cannot be empty.",
        )

    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=serialize_conversation_metadata(request.sources),
        agent_workflow=serialize_conversation_metadata(request.agent_workflow),
        action_result=serialize_conversation_metadata(request.action_result),
    )

    db.add(message)
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)

    return message_to_dict(message)


@app.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
):

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    db.delete(conversation)
    db.commit()

    return {
        "message": "Conversation deleted successfully.",
        "conversation_id": conversation_id,
    }


# =========================================================
# LANGGRAPH STATE
# =========================================================

class WorkspaceState(
    TypedDict
):

    question: str
    context: str
    answer: str


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    try:

        from .mcp.google_drive import (
            get_google_drive_status,
        )

        drive_status = (
            get_google_drive_status()
        )

    except Exception as error:

        drive_status = {
            "configured": False,
            "connected": False,
            "error": str(error),
        }

    return {

        "status": "healthy",

        "rag": "ready",

        "vector_database": "chroma",

        "embedding_model": (
            "all-MiniLM-L6-v2"
        ),

        "llm": "groq",

        "model": GROQ_MODEL,

        "mcp": {
            "google_drive": drive_status
        },
    }


# =========================================================
# DATABASE HEALTH
# =========================================================

@app.get("/database/health")
def database_health():

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return {

            "status": "healthy",

            "database": "PostgreSQL",

            "database_name": (
                "enterprise_ai"
            ),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "PostgreSQL connection failed: "
                f"{str(error)}"
            ),
        )


# =========================================================
# TEXT EXTRACTION
# =========================================================

def extract_text(
    file_path: Path,
    extension: str,
) -> str:

    if extension == ".pdf":

        reader = PdfReader(
            str(file_path)
        )

        text_parts = []

        for page in reader.pages:

            page_text = (
                page.extract_text()
            )

            if page_text:

                text_parts.append(
                    page_text
                )

        return "\n\n".join(
            text_parts
        ).strip()

    if extension == ".docx":

        document = DocxDocument(
            str(file_path)
        )

        text_parts = []

        for paragraph in (
            document.paragraphs
        ):

            paragraph_text = (
                paragraph.text.strip()
            )

            if paragraph_text:

                text_parts.append(
                    paragraph_text
                )

        for table in document.tables:

            for row in table.rows:

                row_text = []

                for cell in row.cells:

                    cell_text = (
                        cell.text.strip()
                    )

                    if cell_text:

                        row_text.append(
                            cell_text
                        )

                if row_text:

                    text_parts.append(
                        " | ".join(
                            row_text
                        )
                    )

        return "\n".join(
            text_parts
        ).strip()

    if extension == ".txt":

        return file_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).strip()

    raise HTTPException(
        status_code=400,
        detail=(
            "Text extraction is not supported "
            "for this file type."
        ),
    )


# =========================================================
# CHUNKING
# =========================================================

def chunk_text(
    document_text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[str]:

    if not document_text:

        return []

    document_text = (
        document_text.strip()
    )

    chunks = []

    start = 0

    text_length = len(
        document_text
    )

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = document_text[
            start:end
        ].strip()

        if chunk:

            chunks.append(
                chunk
            )

        if end >= text_length:

            break

        start = (
            end - overlap
        )

    return chunks


# =========================================================
# VECTOR DOCUMENT ID
# =========================================================

def make_document_id(
    filename: str,
) -> str:

    return filename.replace(
        " ",
        "_",
    )


# =========================================================
# REMOVE OLD VECTOR DATA
# =========================================================

def remove_document_from_vector_db(
    filename: str,
):

    try:

        documents_collection.delete(
            where={
                "filename": filename
            }
        )

    except Exception as error:

        print(
            "Warning: unable to remove "
            f"old vectors: {error}"
        )


# =========================================================
# INDEX DOCUMENT
# =========================================================

def index_document(
    filename: str,
    file_type: str,
    document_text: str,
):

    if not document_text.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "The document contains "
                "no extractable text."
            ),
        )

    remove_document_from_vector_db(
        filename
    )

    chunks = chunk_text(
        document_text
    )

    if not chunks:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to create text chunks."
            ),
        )

    embeddings = embedding_model.encode(
        chunks,
        show_progress_bar=False,
    )

    document_id = make_document_id(
        filename
    )

    ids = [
        f"{document_id}_chunk_{index}"
        for index in range(
            len(chunks)
        )
    ]

    metadatas = []

    for index in range(
        len(chunks)
    ):

        metadatas.append(
            {
                "filename": filename,
                "file_type": file_type,
                "chunk_index": index,
            }
        )

    documents_collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )

    return {
        "filename": filename,
        "chunks": len(chunks),
        "message": (
            "Document indexed successfully."
        ),
    }


# =========================================================
# UPLOAD DOCUMENT
# =========================================================

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Please upload PDF, DOCX or TXT."
            ),
        )

    safe_filename = Path(
        file.filename
    ).name

    file_path = (
        UPLOAD_DIR
        / safe_filename
    )

    contents = await file.read()

    with open(
        file_path,
        "wb",
    ) as output_file:

        output_file.write(
            contents
        )

    try:

        extracted_text = extract_text(
            file_path,
            extension,
        )

    except Exception as error:

        if file_path.exists():

            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to extract document text: "
                f"{str(error)}"
            ),
        )

    try:

        indexing_result = index_document(
            filename=safe_filename,
            file_type=(
                extension
                .replace(".", "")
                .upper()
            ),
            document_text=extracted_text,
        )

    except HTTPException:

        if file_path.exists():

            file_path.unlink()

        raise

    except Exception as error:

        if file_path.exists():

            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                "Document indexing failed: "
                f"{str(error)}"
            ),
        )

    try:

        existing_document = (
            db.query(Document)
            .filter(
                Document.filename
                == safe_filename
            )
            .first()
        )

        if existing_document:

            existing_document.file_type = (
                extension
                .replace(".", "")
                .upper()
            )

            existing_document.file_size = (
                len(contents)
            )

            existing_document.text_length = (
                len(extracted_text)
            )

            existing_document.processing_status = (
                "processed"
            )

            existing_document.extracted_text = (
                extracted_text
            )

        else:

            document_record = Document(
                filename=safe_filename,
                file_type=(
                    extension
                    .replace(".", "")
                    .upper()
                ),
                file_size=len(contents),
                text_length=len(
                    extracted_text
                ),
                processing_status="processed",
                extracted_text=(
                    extracted_text
                ),
            )

            db.add(
                document_record
            )

        db.commit()

    except Exception as error:

        db.rollback()

        print(
            "Warning: PostgreSQL storage failed: "
            f"{error}"
        )

    return {

        "message": (
            "Document uploaded, extracted "
            "and indexed successfully."
        ),

        "filename": safe_filename,

        "file_type": (
            extension
            .replace(".", "")
            .upper()
        ),

        "size": len(contents),

        "text_length": len(
            extracted_text
        ),

        "chunks": indexing_result[
            "chunks"
        ],

        "text": extracted_text,
    }


# =========================================================
# LIST DOCUMENTS
# =========================================================

@app.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
):

    documents = []

    db_documents = (
        db.query(Document)
        .order_by(
            Document.created_at.desc(),
            Document.id.desc(),
        )
        .all()
    )

    if db_documents:

        for document in db_documents:

            file_path = (
                UPLOAD_DIR
                / document.filename
            )

            if (
                file_path.exists()
                and file_path.is_file()
            ):

                documents.append(
                    {
                        "filename": (
                            document.filename
                        ),
                        "file_type": (
                            document.file_type
                        ),
                        "size": (
                            document.file_size
                        ),
                    }
                )

        return {
            "documents": documents
        }

    for file_path in (
        UPLOAD_DIR.iterdir()
    ):

        if file_path.is_file():

            documents.append(
                {
                    "filename": (
                        file_path.name
                    ),
                    "file_type": (
                        file_path.suffix
                        .replace(".", "")
                        .upper()
                    ),
                    "size": (
                        file_path.stat()
                        .st_size
                    ),
                }
            )

    return {
        "documents": documents
    }


# =========================================================
# GET DOCUMENT TEXT
# =========================================================

@app.get(
    "/documents/{filename}/text"
)
def get_document_text(
    filename: str,
):

    safe_filename = Path(
        filename
    ).name

    file_path = (
        UPLOAD_DIR
        / safe_filename
    )

    if (
        not file_path.exists()
        or not file_path.is_file()
    ):

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    extension = (
        file_path.suffix.lower()
    )

    try:

        extracted_text = extract_text(
            file_path,
            extension,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to extract document text: "
                f"{str(error)}"
            ),
        )

    return {

        "filename": safe_filename,

        "file_type": (
            extension
            .replace(".", "")
            .upper()
        ),

        "text_length": len(
            extracted_text
        ),

        "text": extracted_text,
    }


# =========================================================
# GET DOCUMENT CONTENT
# =========================================================

@app.get(
    "/documents/{filename}/content"
)
def get_document_content(
    filename: str,
):

    return get_document_text(
        filename
    )


# =========================================================
# INDEX EXISTING DOCUMENT
# =========================================================

@app.post(
    "/documents/{filename}/index"
)
def index_existing_document(
    filename: str,
):

    safe_filename = Path(
        filename
    ).name

    file_path = (
        UPLOAD_DIR
        / safe_filename
    )

    if (
        not file_path.exists()
        or not file_path.is_file()
    ):

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    extension = (
        file_path.suffix.lower()
    )

    try:

        extracted_text = extract_text(
            file_path,
            extension,
        )

        return index_document(
            filename=safe_filename,
            file_type=(
                extension
                .replace(".", "")
                .upper()
            ),
            document_text=extracted_text,
        )

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to index document: "
                f"{str(error)}"
            ),
        )


# =========================================================
# SEARCH
# =========================================================

@app.post("/search")
def search_documents(
    request: SearchRequest,
):

    query = request.query.strip()

    if not query:

        raise HTTPException(
            status_code=400,
            detail=(
                "Search query cannot be empty."
            ),
        )

    top_k = max(
        1,
        min(
            request.top_k,
            20,
        ),
    )

    query_embedding = (
        embedding_model.encode(
            [query],
            show_progress_bar=False,
        )[0]
    )

    results = (
        documents_collection.query(
            query_embeddings=[
                query_embedding.tolist()
            ],
            n_results=top_k,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )
    )

    result_documents = (
        results.get(
            "documents",
            [[]],
        )[0]
    )

    result_metadatas = (
        results.get(
            "metadatas",
            [[]],
        )[0]
    )

    result_distances = (
        results.get(
            "distances",
            [[]],
        )[0]
    )

    matches = []

    for index, document_text in enumerate(
        result_documents
    ):

        metadata = (
            result_metadatas[index]
            if index
            < len(result_metadatas)
            else {}
        )

        distance = (
            result_distances[index]
            if index
            < len(result_distances)
            else None
        )

        matches.append(
            {
                "text": document_text,
                "filename": metadata.get(
                    "filename"
                ),
                "file_type": metadata.get(
                    "file_type"
                ),
                "chunk_index": metadata.get(
                    "chunk_index"
                ),
                "distance": distance,
            }
        )

    return {

        "query": query,

        "results": matches,

        "count": len(matches),
    }


# =========================================================
# QUERY INTENT
# =========================================================

def is_latest_document_query(
    question: str,
) -> bool:

    normalized = (
        question.lower()
        .strip()
    )

    patterns = [

        r"\blatest document\b",

        r"\blatest file\b",

        r"\brecent document\b",

        r"\brecent file\b",

        r"\bnewest document\b",

        r"\bnewest file\b",

        r"\bmost recent document\b",

        r"\bmost recent file\b",
    ]

    return any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in patterns
    )


def is_summary_query(
    question: str,
) -> bool:

    normalized = (
        question.lower()
        .strip()
    )

    patterns = [

        r"\bsummarize\b",

        r"\bsummarise\b",

        r"\bsummary\b",

        r"\boverview\b",

        r"\bbriefly explain\b",
    ]

    return any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in patterns
    )


# =========================================================
# FIND REFERENCED DOCUMENT
# =========================================================

def find_referenced_document(
    question: str,
    db: Session,
):

    documents = (
        db.query(Document)
        .order_by(
            Document.created_at.desc(),
            Document.id.desc(),
        )
        .all()
    )

    if not documents:

        return None

    normalized_question = (
        question.lower()
    )

    for document in documents:

        if (
            document.filename.lower()
            in normalized_question
        ):

            return document

    question_tokens = set(
        re.findall(
            r"[a-z0-9]+",
            normalized_question,
        )
    )

    ignored_tokens = {

        "the",
        "a",
        "an",
        "document",
        "file",
        "pdf",
        "docx",
        "txt",
        "please",
        "summarize",
        "summarise",
        "summary",
        "about",
        "of",
        "for",
        "this",
        "that",
        "give",
        "me",
        "latest",
        "recent",
        "newest",
        "what",
        "who",
        "are",
        "is",
        "in",
        "from",
    }

    best_document = None
    best_score = 0

    for document in documents:

        filename_tokens = set(
            re.findall(
                r"[a-z0-9]+",
                document.filename.lower(),
            )
        )

        filename_tokens -= (
            ignored_tokens
        )

        matched_tokens = (
            filename_tokens
            & question_tokens
        )

        score = len(
            matched_tokens
        )

        if score > best_score:

            best_score = score

            best_document = (
                document
            )

    if best_score > 0:

        return best_document

    return None


# =========================================================
# LATEST DOCUMENT
# =========================================================

def get_latest_document(
    db: Session,
):

    return (
        db.query(Document)
        .order_by(
            Document.created_at.desc(),
            Document.id.desc(),
        )
        .first()
    )


# =========================================================
# RETRIEVE SPECIFIC DOCUMENT
# =========================================================

def retrieve_document_chunks(
    filename: str,
    max_chunks: int,
):

    try:

        results = (
            documents_collection.get(
                where={
                    "filename": filename
                },
                include=[
                    "documents",
                    "metadatas",
                ],
            )
        )

        documents = results.get(
            "documents",
            [],
        )

        metadatas = results.get(
            "metadatas",
            [],
        )

        chunks = []

        for index, document_text in enumerate(
            documents
        ):

            metadata = (
                metadatas[index]
                if index < len(metadatas)
                else {}
            )

            chunks.append(
                {
                    "text": document_text,
                    "filename": filename,
                    "file_type": metadata.get(
                        "file_type"
                    ),
                    "chunk_index": metadata.get(
                        "chunk_index",
                        index,
                    ),
                }
            )

        chunks.sort(
            key=lambda item: item.get(
                "chunk_index",
                0,
            )
        )

        return chunks[
            :max_chunks
        ]

    except Exception as error:

        print(
            "Document retrieval failed: "
            f"{error}"
        )

        return []


# =========================================================
# SEMANTIC RETRIEVAL
# =========================================================

def retrieve_semantic_chunks(
    question: str,
):

    query_embedding = (
        embedding_model.encode(
            [question],
            show_progress_bar=False,
        )[0]
    )

    results = (
        documents_collection.query(
            query_embeddings=[
                query_embedding.tolist()
            ],
            n_results=RETRIEVAL_CANDIDATES,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )
    )

    result_documents = (
        results.get(
            "documents",
            [[]],
        )[0]
    )

    result_metadatas = (
        results.get(
            "metadatas",
            [[]],
        )[0]
    )

    result_distances = (
        results.get(
            "distances",
            [[]],
        )[0]
    )

    retrieved = []

    document_counts = {}

    for index, document_text in enumerate(
        result_documents
    ):

        metadata = (
            result_metadatas[index]
            if index
            < len(result_metadatas)
            else {}
        )

        filename = metadata.get(
            "filename"
        )

        if not filename:

            continue

        current_count = (
            document_counts.get(
                filename,
                0,
            )
        )

        if (
            current_count
            >= MAX_CHUNKS_PER_DOCUMENT
        ):

            continue

        document_counts[
            filename
        ] = (
            current_count + 1
        )

        distance = (
            result_distances[index]
            if index
            < len(result_distances)
            else None
        )

        retrieved.append(
            {
                "text": document_text,
                "filename": filename,
                "file_type": metadata.get(
                    "file_type"
                ),
                "chunk_index": metadata.get(
                    "chunk_index",
                    index,
                ),
                "distance": distance,
            }
        )

        if (
            len(retrieved)
            >= MAX_CONTEXT_CHUNKS
        ):

            break

    return retrieved


# =========================================================
# UNIFIED RETRIEVAL
# =========================================================

def retrieve_chunks(
    question: str,
    db: Session,
):

    if is_latest_document_query(
        question
    ):

        latest_document = (
            get_latest_document(
                db
            )
        )

        if latest_document:

            max_chunks = (
                SUMMARY_MAX_CHUNKS
                if is_summary_query(
                    question
                )
                else DOCUMENT_QUERY_MAX_CHUNKS
            )

            chunks = (
                retrieve_document_chunks(
                    latest_document.filename,
                    max_chunks,
                )
            )

            if chunks:

                return chunks

    referenced_document = (
        find_referenced_document(
            question,
            db,
        )
    )

    if referenced_document:

        max_chunks = (
            SUMMARY_MAX_CHUNKS
            if is_summary_query(
                question
            )
            else DOCUMENT_QUERY_MAX_CHUNKS
        )

        chunks = (
            retrieve_document_chunks(
                referenced_document.filename,
                max_chunks,
            )
        )

        if chunks:

            return chunks

    return retrieve_semantic_chunks(
        question
    )


# =========================================================
# BUILD CONTEXT
# =========================================================

def build_context(
    chunks: List[dict],
) -> str:

    if not chunks:

        return ""

    context_parts = []

    total_characters = 0

    for chunk in chunks:

        filename = chunk.get(
            "filename",
            "Unknown source",
        )

        chunk_index = chunk.get(
            "chunk_index",
            0,
        )

        text_content = chunk.get(
            "text",
            "",
        ).strip()

        if not text_content:

            continue

        section = (
            f"[Source: {filename}]\n"
            f"[Chunk: {chunk_index}]\n"
            f"{text_content}"
        )

        if (
            total_characters
            + len(section)
            > MAX_CONTEXT_CHARACTERS
        ):

            break

        context_parts.append(
            section
        )

        total_characters += (
            len(section)
        )

    return "\n\n".join(
        context_parts
    )


# =========================================================
# BUILD SOURCES
# =========================================================

def build_sources(
    chunks: List[dict],
) -> List[str]:

    sources = []

    for chunk in chunks:

        filename = chunk.get(
            "filename"
        )

        if (
            filename
            and filename not in sources
        ):

            sources.append(
                filename
            )

    return sources


# =========================================================
# CLEAN AI OUTPUT
# =========================================================

def clean_llm_output(
    answer: str,
) -> str:

    if not answer:

        return ""

    answer = re.sub(
        r"<br\s*/?>",
        "\n",
        answer,
        flags=re.IGNORECASE,
    )

    answer = re.sub(
        r"</?(?:div|span|p|li|ul|ol)[^>]*>",
        "",
        answer,
        flags=re.IGNORECASE,
    )

    answer = re.sub(
        r"\n{3,}",
        "\n\n",
        answer,
    )

    return answer.strip()


# =========================================================
# LANGGRAPH AI NODE
# =========================================================

def generate_answer(
    state: WorkspaceState,
):

    question = state[
        "question"
    ]

    context = state[
        "context"
    ]

    if not llm:

        return {
            "answer": (
                "The Groq API is not configured. "
                "Please configure GROQ_API_KEY "
                "in the backend environment."
            )
        }

    if not context:

        return {
            "answer": (
                "I could not find relevant "
                "information in the workspace "
                "knowledge base."
            )
        }

    prompt = f"""
You are the AI assistant for an enterprise
document workspace.

Answer the user's question using ONLY the
provided workspace context.

USER QUESTION:
{question}

WORKSPACE CONTEXT:
{context}

IMPORTANT RULES:

1. Ground your answer only in the provided context.

2. Never invent names, numbers, dates, participants,
   payments, locations, or other facts.

3. If the requested information is present,
   include it accurately.

4. If the user asks for a summary, provide a
   comprehensive summary of the available document.

5. For summaries, preserve important:
   - names
   - participants
   - dates
   - amounts
   - locations
   - events
   - payment information
   - important conditions
   - key takeaways

6. Do not unnecessarily omit important information.

7. Use clean Markdown.

8. You may use:
   - headings
   - bullet lists
   - numbered lists
   - bold text
   - Markdown tables

9. DO NOT generate HTML.

10. DO NOT use:
    <br>
    <br/>
    <p>
    <div>
    <span>
    or any other HTML tags.

11. If the context contains multiple pieces of
    information belonging to the same document,
    combine them into one coherent answer.

12. Do not mention embeddings, chunks, ChromaDB,
    retrieval, vector databases, or internal
    implementation unless explicitly asked.

13. If the requested information is not available
    in the provided context, clearly say so.

Return only the final answer.
"""

    try:

        response = llm.invoke(
            prompt
        )

        raw_answer = (
            response.content
            if hasattr(
                response,
                "content",
            )
            else str(response)
        )

        return {
            "answer": clean_llm_output(
                raw_answer
            )
        }

    except Exception as error:

        print(
            f"LLM generation failed: "
            f"{error}"
        )

        raise


# =========================================================
# LANGGRAPH
# =========================================================

def build_workspace_graph():

    graph = StateGraph(
        WorkspaceState
    )

    graph.add_node(
        "generate_answer",
        generate_answer,
    )

    graph.set_entry_point(
        "generate_answer"
    )

    graph.add_edge(
        "generate_answer",
        END,
    )

    return graph.compile()


workspace_graph = (
    build_workspace_graph()
)


# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):

    question = (
        request.message.strip()
    )

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    chunks = retrieve_chunks(
        question,
        db,
    )

    context = build_context(
        chunks
    )

    sources = build_sources(
        chunks
    )

    try:

        result = workspace_graph.invoke(
            {
                "question": question,
                "context": context,
                "answer": "",
            }
        )

        answer = clean_llm_output(
            result.get(
                "answer",
                "",
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "AI response generation failed: "
                f"{str(error)}"
            ),
        )

    return {

        "message": question,

        "answer": answer,

        "sources": sources,

        "retrieved_chunks": len(
            chunks
        ),
    }


# =========================================================
# RAG STATUS
# =========================================================

@app.get("/rag/status")
def rag_status():

    try:

        count = (
            documents_collection.count()
        )

        return {

            "status": "ready",

            "collection": (
                "enterprise_documents"
            ),

            "chunks": count,

            "embedding_model": (
                "all-MiniLM-L6-v2"
            ),

            "vector_database": "ChromaDB",
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to read RAG status: "
                f"{str(error)}"
            ),
        )


# =========================================================
# DELETE DOCUMENT
# =========================================================

@app.delete(
    "/documents/{filename}"
)
def delete_document(
    filename: str,
    db: Session = Depends(get_db),
):

    safe_filename = Path(
        filename
    ).name

    file_path = (
        UPLOAD_DIR
        / safe_filename
    )

    if (
        not file_path.exists()
        or not file_path.is_file()
    ):

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    remove_document_from_vector_db(
        safe_filename
    )

    try:

        document_record = (
            db.query(Document)
            .filter(
                Document.filename
                == safe_filename
            )
            .first()
        )

        if document_record:

            db.delete(
                document_record
            )

            db.commit()

    except Exception as error:

        db.rollback()

        print(
            "Warning: PostgreSQL deletion failed: "
            f"{error}"
        )

    file_path.unlink()

    return {

        "message": (
            "Document deleted successfully."
        ),

        "filename": safe_filename,
    }


# =========================================================
# GOOGLE DRIVE MCP
# =========================================================

@app.get(
    "/mcp/google/status"
)
def google_drive_mcp_status():

    try:

        from .mcp.google_drive import (
            get_google_drive_status,
        )

        return (
            get_google_drive_status()
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to read Google Drive MCP "
                f"status: {error}"
            ),
        )


# =========================================================
# GOOGLE DRIVE MCP AUTHORIZATION
# =========================================================

@app.get(
    "/mcp/google/authorize"
)
def google_drive_authorize():

    try:

        from .mcp.google_drive import (
            create_google_authorization_url,
        )

        authorization_url = (
            create_google_authorization_url()
        )

        return {

            "message": (
                "Open the authorization_url "
                "in your browser to connect "
                "Google Drive."
            ),

            "authorization_url": (
                authorization_url
            ),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create Google OAuth "
                f"authorization URL: {error}"
            ),
        )


# =========================================================
# GOOGLE DRIVE MCP CALLBACK
# =========================================================

@app.get(
    "/mcp/google/callback"
)
async def google_drive_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):

    if error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Google authorization failed: "
                f"{error}"
            ),
        )

    if not code:

        raise HTTPException(
            status_code=400,
            detail=(
                "Google authorization code "
                "was not provided."
            ),
        )

    try:

        from .mcp.google_drive import (
            exchange_authorization_code,
            validate_oauth_state,
        )

        if not state:

            raise HTTPException(
                status_code=400,
                detail=(
                    "OAuth state parameter "
                    "is missing."
                ),
            )

        if not validate_oauth_state(
            state
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid or expired OAuth state."
                ),
            )

        await exchange_authorization_code(
            code
        )

        return {

            "status": "connected",

            "message": (
                "Google Drive MCP authorization "
                "completed successfully."
            ),

            "next_step": (
                "You can now use the Google Drive "
                "MCP endpoints or ask the Knowledge "
                "Agent questions about Google Drive."
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Google Drive OAuth callback failed: "
                f"{error}"
            ),
        )


# =========================================================
# GOOGLE DRIVE MCP TOOLS
# =========================================================

@app.get(
    "/mcp/google/tools"
)
async def google_drive_mcp_tools():

    try:

        from .mcp.google_drive import (
            list_google_drive_tools,
        )

        tools = (
            await list_google_drive_tools()
        )

        return {

            "server": (
                "Google Drive MCP"
            ),

            "endpoint": (
                "https://drivemcp.googleapis.com/mcp/v1"
            ),

            "tools": tools,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to list Google Drive MCP "
                f"tools: {error}"
            ),
        )


# =========================================================
# GOOGLE DRIVE MCP RECENT FILES
# =========================================================

@app.get(
    "/mcp/google/recent"
)
async def google_drive_mcp_recent(
    max_files: int = 10,
):

    max_files = max(
        1,
        min(
            max_files,
            50,
        ),
    )

    try:

        from .mcp.google_drive import (
            list_recent_google_drive_files,
        )

        result = (
            await list_recent_google_drive_files(
                max_files=max_files
            )
        )

        return {

            "source": (
                "Google Drive MCP"
            ),

            "tool": (
                "list_recent_files"
            ),

            "max_files": max_files,

            "result": result,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to list recent Google Drive "
                f"files: {error}"
            ),
        )


# =========================================================
# GOOGLE DRIVE MCP SEARCH
# =========================================================

@app.post(
    "/mcp/google/search"
)
async def google_drive_mcp_search(
    request: DriveSearchRequest,
):

    query = (
        request.query.strip()
    )

    if not query:

        raise HTTPException(
            status_code=400,
            detail=(
                "Google Drive search query "
                "cannot be empty."
            ),
        )

    max_files = max(
        1,
        min(
            request.max_files,
            20,
        ),
    )

    try:

        from .mcp.google_drive import (
            search_and_read_google_drive,
        )

        results = (
            await search_and_read_google_drive(
                query,
                max_files=max_files,
            )
        )

        return {

            "query": query,

            "source": (
                "Google Drive MCP"
            ),

            "max_files": max_files,

            "results": results,

            "count": len(results),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Google Drive MCP search failed: "
                f"{error}"
            ),
        )


# =========================================================
# GOOGLE DRIVE MCP READ FILE
# =========================================================

@app.get(
    "/mcp/google/files/{file_id}"
)
async def google_drive_mcp_read_file(
    file_id: str,
):

    if not file_id.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "Google Drive file ID "
                "cannot be empty."
            ),
        )

    try:

        from .mcp.google_drive import (
            read_google_drive_file,
        )

        result = (
            await read_google_drive_file(
                file_id
            )
        )

        return {

            "source": (
                "Google Drive MCP"
            ),

            "result": result,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Google Drive MCP file read failed: "
                f"{error}"
            ),
        )


# =========================================================
# GMAIL MCP
# =========================================================

@app.get("/mcp/gmail/status")
def gmail_mcp_status():
    try:
        from .mcp.gmail import get_gmail_status
        return get_gmail_status()
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Unable to read Gmail MCP status: {error}")

@app.get("/mcp/gmail/authorize")
def gmail_authorize():
    try:
        from .mcp.gmail import create_gmail_authorization_url
        authorization_url = create_gmail_authorization_url()
        return {"message": "Open the authorization_url in your browser to connect Gmail.", "authorization_url": authorization_url}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Unable to create Gmail OAuth authorization URL: {error}")

@app.get("/mcp/gmail/callback")
async def gmail_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Google Gmail authorization failed: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Google Gmail authorization code was not provided.")
    try:
        from .mcp.gmail import exchange_gmail_authorization_code, validate_gmail_oauth_state
        if not state:
            raise HTTPException(status_code=400, detail="OAuth state parameter is missing.")
        if not validate_gmail_oauth_state(state):
            raise HTTPException(status_code=400, detail="Invalid or expired Gmail OAuth state.")
        await exchange_gmail_authorization_code(code)
        return {"status": "connected", "message": "Gmail MCP authorization completed successfully.", "next_step": "You can now use Gmail MCP endpoints for searching threads, reading threads, and creating drafts."}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Gmail OAuth callback failed: {error}")

@app.get("/mcp/gmail/tools")
async def gmail_mcp_tools():
    try:
        from .mcp.gmail import list_gmail_tools
        tools = await list_gmail_tools()
        return {"server": "Gmail MCP", "endpoint": "https://gmailmcp.googleapis.com/mcp/v1", "tools": tools}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Unable to list Gmail MCP tools: {error}")

@app.get("/mcp/gmail/search")
async def gmail_mcp_search(query: str, max_results: int = 10):
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Gmail search query cannot be empty.")
    max_results = max(1, min(max_results, 50))
    try:
        from .mcp.gmail import search_gmail_threads
        results = await search_gmail_threads(query, max_results=max_results)
        return {"query": query, "source": "Gmail MCP", "max_results": max_results, "results": results, "count": len(results) if isinstance(results, list) else None}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Gmail MCP search failed: {error}")

@app.get("/mcp/gmail/threads/{thread_id}")
async def gmail_mcp_thread(thread_id: str):
    if not thread_id.strip():
        raise HTTPException(status_code=400, detail="Gmail thread ID cannot be empty.")
    try:
        from .mcp.gmail import get_gmail_thread
        result = await get_gmail_thread(thread_id)
        return {"source": "Gmail MCP", "thread_id": thread_id, "result": result}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Gmail MCP thread read failed: {error}")

@app.get("/mcp/gmail/labels")
async def gmail_mcp_labels():
    try:
        from .mcp.gmail import list_gmail_labels
        labels = await list_gmail_labels()
        return {"source": "Gmail MCP", "labels": labels}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Unable to list Gmail labels: {error}")

@app.get("/mcp/gmail/drafts")
async def gmail_mcp_drafts(max_results: int = 10):
    max_results = max(1, min(max_results, 50))
    try:
        from .mcp.gmail import list_gmail_drafts
        drafts = await list_gmail_drafts(max_results=max_results)
        return {"source": "Gmail MCP", "max_results": max_results, "drafts": drafts}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Unable to list Gmail drafts: {error}")

class GmailDraftRequest(BaseModel):
    to: str
    subject: str
    body: str
    cc: str | None = None
    bcc: str | None = None

@app.post("/mcp/gmail/draft")
async def gmail_mcp_create_draft(request: GmailDraftRequest):
    if not request.to.strip():
        raise HTTPException(status_code=400, detail="Recipient cannot be empty.")
    if not request.subject.strip():
        raise HTTPException(status_code=400, detail="Subject cannot be empty.")
    if not request.body.strip():
        raise HTTPException(status_code=400, detail="Email body cannot be empty.")
    try:
        from .mcp.gmail import create_gmail_draft
        result = await create_gmail_draft(to=request.to, subject=request.subject, body=request.body, cc=request.cc, bcc=request.bcc)
        return {"source": "Gmail MCP", "status": "draft_created", "result": result}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Unable to create Gmail draft: {error}")


# =========================================================
# MULTI-AGENT WORKFLOW
# =========================================================

@app.post("/agents/run")
def run_multi_agent(
    request: ChatRequest,
):

    """
    Execute the LangGraph multi-agent workflow.

    Flow:

        Supervisor Agent
              ↓
        Knowledge Agent
        ├── ChromaDB
        └── Google Drive MCP
              ↓
        Response Agent
    """

    from app.agents.orchestrator import (
        run_agent_workflow,
    )

    try:

        result = run_agent_workflow(
            request.message
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Multi-agent workflow failed: "
                f"{exc}"
            ),
        )
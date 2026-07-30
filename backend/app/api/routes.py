from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Header
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.responses import JSONResponse
import os
from app.models.schemas import (
    ChatRequest, ChatResponse, ResetResponse, HealthResponse, Source,
    IngestResponse, RegisterRequest, LoginRequest, AuthResponse,
    UserResponse, ConversationSummary, ConversationDetail,
    UserSettingsUpdate, ConversationRename, SearchRequest,
    GoogleAuthRequest,
)
from app.services.llm_service import LLMService
from app.services.ingestion_service import IngestionService
from app.services.auth_service import (
    authenticate_user, create_user, get_user_by_email,
    get_user_by_username, create_access_token, get_user_from_token,
    google_auth,
)
from app.services.chat_history_service import ChatHistoryService
from app.core.config import Settings
from app.dependencies import get_settings, get_llm_service, get_ingestion_service, get_file_processor
from app.database.connection import get_db
from app.database.models import ConversationFile
from app.services.file_processor import FileProcessor

router = APIRouter()


def get_current_user(token: str, db: Session):
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def extract_token(authorization: str) -> str:
    if not authorization:
        return ""
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return authorization


# ─── AUTH ROUTES ───────────────────────────────────────────────────────────
@router.post("/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, request.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if get_user_by_username(db, request.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = create_user(db, request.email, request.username, request.password, request.full_name)
    token = create_access_token({"sub": user.email})
    return AuthResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "created_at": str(user.created_at),
        },
    )


@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return AuthResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "created_at": str(user.created_at),
        },
    )


@router.post("/auth/google", response_model=AuthResponse)
async def google_login(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    result = google_auth(db, request.credential)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    user, token = result
    return AuthResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "created_at": str(user.created_at),
        },
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        created_at=user.created_at,
    )


# ─── CONVERSATION ROUTES ───────────────────────────────────────────────────
@router.get("/conversations")
async def list_conversations(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    chat_service = ChatHistoryService(db)
    conversations = chat_service.get_user_conversations(user.id)
    return [
        {
            "id": conv.id,
            "title": conv.title,
            "created_at": str(conv.created_at),
            "updated_at": str(conv.updated_at),
            "message_count": len(conv.messages),
        }
        for conv in conversations
    ]


@router.post("/conversations")
async def create_conversation(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    chat_service = ChatHistoryService(db)
    conv = chat_service.create_conversation(user.id)
    return {"id": conv.id, "title": conv.title, "created_at": str(conv.created_at)}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    chat_service = ChatHistoryService(db)
    conv = chat_service.get_conversation(conversation_id, user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = chat_service.get_conversation_messages(conversation_id, user.id)
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": str(conv.created_at),
        "messages": [
            {"role": m.role, "content": m.content, "created_at": str(m.created_at)}
            for m in messages
        ],
    }


@router.put("/conversations/{conversation_id}/title")
async def rename_conversation(conversation_id: int, request: ConversationRename, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    chat_service = ChatHistoryService(db)
    success = chat_service.update_conversation_title(conversation_id, user.id, request.title)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Title updated"}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    chat_service = ChatHistoryService(db)
    success = chat_service.delete_conversation(conversation_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}


@router.get("/conversations/search/{query}")
async def search_conversations(query: str, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    chat_service = ChatHistoryService(db)
    conversations = chat_service.search_conversations(user.id, query)
    return [
        {"id": conv.id, "title": conv.title, "updated_at": str(conv.updated_at)}
        for conv in conversations
    ]


# ─── FILE UPLOAD ROUTE ─────────────────────────────────────────────────────
@router.post("/upload")
async def upload_file(
    authorization: str = Header(default=""),
    file: Optional[UploadFile] = None,
    title: Optional[str] = None,
    file_processor: FileProcessor = Depends(get_file_processor),
    db: Session = Depends(get_db),
):
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if not title:
        title = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename

    os.makedirs("temp_uploads", exist_ok=True)
    file_path = f"temp_uploads/{file.filename}"

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        result = file_processor.process_file(file_path, title)
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "chunks": result.get("chunks", 0),
            "source": result.get("source", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ─── CHAT ROUTE ───────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: str = Header(default=""),
    llm_service: LLMService = Depends(get_llm_service),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    chat_service = ChatHistoryService(db)

    if request.conversation_id:
        conv = chat_service.get_conversation(request.conversation_id, user.id)
        if not conv:
            conv = chat_service.create_conversation(user.id)
    else:
        conv = chat_service.create_conversation(user.id)

    chat_service.add_message(conv.id, "user", request.message)

    if request.file_sources:
        for src in request.file_sources:
            existing = db.query(ConversationFile).filter(
                ConversationFile.conversation_id == conv.id,
                ConversationFile.source == src
            ).first()
            if not existing:
                cf = ConversationFile(
                    conversation_id=conv.id,
                    filename=src.split(":", 1)[1] if ":" in src else src,
                    source=src,
                    ocr_text="",
                )
                db.add(cf)
        db.commit()

    file_contexts = db.query(ConversationFile).filter(
        ConversationFile.conversation_id == conv.id
    ).all()

    history = chat_service.get_history_for_llm(conv.id)
    context = llm_service.retrieval_service.get_context(request.message)
    sources = llm_service.retrieval_service.query(request.message)

    system_prompt = llm_service.system_prompt.format(disclaimer=settings.HEALTH_DISCLAIMER)

    file_context_parts = []
    for fc in file_contexts:
        file_chunks = llm_service.retrieval_service.query_by_source(fc.source)
        if file_chunks:
            chunk_texts = "\n".join(c["content"] for c in file_chunks)
            file_context_parts.append(f"Uploaded file ({fc.filename}):\n{chunk_texts}")
    if file_context_parts:
        system_prompt += f"\n\nUploaded file context:\n" + "\n\n".join(file_context_parts)

    if context:
        system_prompt += f"\n\nRelevant medical context:\n{context}"

    if settings.ENABLE_SCRAPER:
        try:
            from app.services.scraper import MedicalScraper
            scraper = MedicalScraper()
            try:
                scraper_sources = scraper.get_structured_info(request.message)
                if scraper_sources:
                    sources.extend(scraper_sources)
            finally:
                scraper.close()
        except Exception:
            pass

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)

    response = llm_service.client.chat.complete(
        model=settings.MISTRAL_MODEL,
        messages=messages,
        max_tokens=settings.MAX_TOKENS,
        temperature=settings.TEMPERATURE,
    )

    reply = response.choices[0].message.content.strip()
    sources_str = str(sources) if sources else ""
    chat_service.add_message(conv.id, "assistant", reply, sources_str)

    return ChatResponse(
        reply=reply,
        conversation_id=conv.id,
        disclaimer=settings.HEALTH_DISCLAIMER,
        sources=[Source(**s) for s in sources] if sources else None,
        title=conv.title,
    )


# ─── RESET ROUTE ──────────────────────────────────────────────────────────
@router.post("/reset", response_model=ResetResponse)
async def reset_conversation(
    conversation_id: int,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    token = extract_token(authorization)
    user = get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    chat_service = ChatHistoryService(db)
    conv = chat_service.get_conversation(conversation_id, user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    for msg in conv.messages:
        db.delete(msg)
    db.commit()

    return ResetResponse(message="Conversation reset", conversation_id=conv.id)


# ─── HEALTH / INGEST / STATS ──────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    return HealthResponse(status="healthy", version=settings.APP_VERSION)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    directory: str = "data/medical_knowledge",
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    import os
    if not os.path.isdir(directory):
        return IngestResponse(success=False, message=f"Directory not found: {directory}", chunks_ingested=0)
    chunks = ingestion_service.ingest_directory(directory)
    stats = ingestion_service.get_collection_stats()
    return IngestResponse(success=True, message=f"Ingested {chunks} chunks", chunks_ingested=chunks, total_chunks=stats["total_chunks"])


@router.get("/stats", response_model=dict)
async def get_stats(ingestion_service: IngestionService = Depends(get_ingestion_service)):
    return ingestion_service.get_collection_stats()


@router.post("/search-medical")
async def search_medical(query: str, db: Session = Depends(get_db)):
    from app.services.scraper import MedicalScraper
    scraper = MedicalScraper()
    try:
        result = scraper.scrape_medical_info(query)
        return {"query": query, "results": result}
    finally:
        scraper.close()

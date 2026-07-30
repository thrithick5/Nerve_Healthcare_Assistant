from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.database.models import Conversation, Message


class ChatHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_conversations(self, user_id: int):
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    def get_conversation(self, conversation_id: int, user_id: int) -> Optional[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )

    def create_conversation(self, user_id: int, title: str = "New Conversation") -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def add_message(self, conversation_id: int, role: str, content: str, sources: str = "") -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.updated_at = datetime.utcnow()
            if conv.title == "New Conversation" and role == "user":
                conv.title = content[:80] + ("..." if len(content) > 80 else "")
            self.db.commit()

        return msg

    def get_conversation_messages(self, conversation_id: int, user_id: int):
        conv = self.get_conversation(conversation_id, user_id)
        if not conv:
            return []
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )

    def get_history_for_llm(self, conversation_id: int, limit: int = 30):
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit * 2)
            .all()
        )
        messages.reverse()
        return [{"role": m.role, "content": m.content} for m in messages]

    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        conv = self.get_conversation(conversation_id, user_id)
        if not conv:
            return False
        self.db.delete(conv)
        self.db.commit()
        return True

    def update_conversation_title(self, conversation_id: int, user_id: int, title: str):
        conv = self.get_conversation(conversation_id, user_id)
        if conv:
            conv.title = title
            self.db.commit()
            return True
        return False

    def search_conversations(self, user_id: int, query: str):
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Conversation.title.ilike(f"%{query}%")
            )
            .order_by(Conversation.updated_at.desc())
            .all()
        )

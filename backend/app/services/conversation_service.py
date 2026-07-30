import uuid
from datetime import datetime
from typing import Optional
from app.core.config import Settings
from app.models.schemas import Conversation, Message


class ConversationService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._conversations: dict[str, Conversation] = {}

    def create_conversation(self) -> Conversation:
        conv = Conversation(
            id=str(uuid.uuid4()),
            messages=[]
        )
        self._conversations[conv.id] = conv
        return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    def add_message(self, conversation_id: str, role: str, content: str) -> Conversation:
        conv = self.get_conversation(conversation_id)
        if not conv:
            conv = self.create_conversation()

        message = Message(role=role, content=content)
        conv.messages.append(message)
        conv.updated_at = datetime.now()

        if len(conv.messages) > self.settings.MAX_HISTORY_LENGTH * 2:
            conv.messages = conv.messages[-(self.settings.MAX_HISTORY_LENGTH * 2):]

        return conv

    def get_history(self, conversation_id: str) -> list[dict]:
        conv = self.get_conversation(conversation_id)
        if not conv:
            return []
        return [
            {"role": msg.role, "content": msg.content}
            for msg in conv.messages[-self.settings.MAX_HISTORY_LENGTH:]
        ]

    def reset_conversation(self, conversation_id: str) -> Conversation:
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.messages = []
            conv.updated_at = datetime.now()
            return conv
        return self.create_conversation()

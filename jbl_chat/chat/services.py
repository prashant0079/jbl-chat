from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .models import Conversation, Message


def get_or_create_conversation(me, other) -> Conversation:
    if me == other:
        raise ValueError("Cannot start a conversation with yourself.")
    user_low, user_high = (me, other) if me.id < other.id else (other, me)
    conversation, _created = Conversation.objects.get_or_create(
        user1=user_low,
        user2=user_high,
    )
    return conversation


def can_access_conversation(conversation: Conversation, user) -> bool:
    return conversation.user1_id == user.id or conversation.user2_id == user.id


def send_message(conversation: Conversation, sender, body: str) -> Message:
    with transaction.atomic():
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            body=body,
        )
        Conversation.objects.filter(id=conversation.id).update(
            last_message_at=message.created_at or timezone.now(),
            last_message_id=message.id,
        )
        conversation.last_message_at = message.created_at
        conversation.last_message_id = message.id
    return message

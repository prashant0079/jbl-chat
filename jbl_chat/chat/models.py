from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Conversation(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_user1",
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_user2",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user1", "user2"], name="unique_conversation_pair"
            ),
            models.CheckConstraint(
                check=Q(user1__lt=F("user2")),
                name="user1_less_than_user2",
            ),
        ]
        ordering = ["-last_message_at", "-id"]

    def save(self, *args, **kwargs):
        # Enforce stable ordering for the participant pair.
        if self.user1_id is not None and self.user2_id is not None:
            if self.user1_id > self.user2_id:
                self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Conversation({self.user1_id}, {self.user2_id})"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="messages_sent",
        on_delete=models.CASCADE,
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["conversation", "id"]),
        ]

    def __str__(self) -> str:
        return f"Message({self.id})"

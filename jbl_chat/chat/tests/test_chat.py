from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from chat import services
from chat.models import Conversation, Message


User = get_user_model()


class ChatServicesTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pw")
        self.bob = User.objects.create_user(username="bob", password="pw")

    def test_get_or_create_orders_participants_and_deduplicates(self):
        conv = services.get_or_create_conversation(self.bob, self.alice)
        self.assertLess(conv.user1_id, conv.user2_id)

        conv_again = services.get_or_create_conversation(self.alice, self.bob)
        self.assertEqual(conv.id, conv_again.id)

    def test_get_or_create_rejects_self_conversation(self):
        with self.assertRaises(ValueError):
            services.get_or_create_conversation(self.alice, self.alice)

    def test_send_message_updates_denormalized_fields(self):
        conv = services.get_or_create_conversation(self.alice, self.bob)
        message = services.send_message(conv, self.alice, "hello there")

        conv.refresh_from_db()
        self.assertEqual(conv.last_message_id, message.id)
        self.assertIsNotNone(conv.last_message_at)
        self.assertEqual(Message.objects.count(), 1)


class ChatViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.alice = User.objects.create_user(username="alice", password="pw")
        self.bob = User.objects.create_user(username="bob", password="pw")
        self.charlie = User.objects.create_user(username="charlie", password="pw")
        self.client.login(username="alice", password="pw")

    def test_users_list_shows_other_users(self):
        resp = self.client.get(reverse("chat:users_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.bob.username)
        self.assertNotContains(resp, f"ID: {self.alice.id}")

    def test_conversation_detail_creates_conversation(self):
        self.assertEqual(Conversation.objects.count(), 0)
        resp = self.client.get(reverse("chat:conversation_detail", args=[self.bob.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertContains(resp, self.bob.username)

    def test_send_message_hx_sets_denorm_fields(self):
        url = reverse("chat:send_message", args=[self.bob.id])
        resp = self.client.post(
            url,
            {"body": "hey bob"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)
        message = Message.objects.get()
        conv = Conversation.objects.get()
        self.assertEqual(conv.last_message_id, message.id)
        self.assertContains(resp, "hey bob")

    def test_send_message_non_hx_redirects(self):
        url = reverse("chat:send_message", args=[self.bob.id])
        resp = self.client.post(url, {"body": "plain post"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("chat:conversation_detail", args=[self.bob.id]), resp["Location"])

    def test_poll_messages_respects_after_param(self):
        conv = services.get_or_create_conversation(self.alice, self.bob)
        first = services.send_message(conv, self.alice, "first")
        services.send_message(conv, self.bob, "second")

        poll_url = reverse("chat:poll_messages", args=[self.bob.id])
        resp = self.client.get(poll_url, {"after": first.id})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotIn("first", content)
        self.assertIn("second", content)

    def test_poll_messages_returns_empty_when_none_new(self):
        conv = services.get_or_create_conversation(self.alice, self.bob)
        last = services.send_message(conv, self.alice, "only")

        poll_url = reverse("chat:poll_messages", args=[self.bob.id])
        resp = self.client.get(poll_url, {"after": last.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode().strip(), "")

    def test_access_control_blocks_non_participant(self):
        conv = services.get_or_create_conversation(self.alice, self.bob)
        services.send_message(conv, self.alice, "hi")

        # Charlie should not be able to poll this conversation
        self.client.logout()
        self.client.login(username="charlie", password="pw")
        poll_url = reverse("chat:poll_messages", args=[self.bob.id])
        resp = self.client.get(poll_url)
        self.assertEqual(resp.status_code, 404)

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from chat import services


class Command(BaseCommand):
    help = "Seed demo users and sample chat history. Safe to run multiple times."

    def handle(self, *args, **options):
        User = get_user_model()
        users_data = [
            ("alice", "password123", "alice@example.com"),
            ("bob", "password123", "bob@example.com"),
            ("charlie", "password123", "charlie@example.com"),
        ]

        created = []
        users = {}
        for username, password, email in users_data:
            user, made = User.objects.get_or_create(
                username=username,
                defaults={"email": email},
            )
            if made:
                user.set_password(password)
                user.save()
                created.append(username)
            users[username] = user

        self.stdout.write(self.style.SUCCESS(f"Users ready: {', '.join(users.keys())}"))
        if created:
            self.stdout.write(self.style.NOTICE(f"Created new users: {', '.join(created)}"))

        alice = users["alice"]
        bob = users["bob"]
        charlie = users["charlie"]

        # Seed Alice <-> Bob conversation if empty.
        conv_ab = services.get_or_create_conversation(alice, bob)
        if not conv_ab.messages.exists():
            for sender, body in [
                (alice, "Hey Bob, welcome to jbl-chat!"),
                (bob, "Hi Alice, looks slick with HTMX updates."),
                (alice, "Try sending a message and watch the list update."),
            ]:
                services.send_message(conv_ab, sender, body)
            self.stdout.write(self.style.SUCCESS("Seeded conversation: alice ↔ bob"))
        else:
            self.stdout.write("alice ↔ bob already has messages; skipped seeding.")

        # Seed Bob <-> Charlie conversation if empty.
        conv_bc = services.get_or_create_conversation(bob, charlie)
        if not conv_bc.messages.exists():
            for sender, body in [
                (charlie, "Hey Bob, testing incremental polling."),
                (bob, "Confirmed—it only fetches messages after last id."),
                (charlie, "Great!"),
            ]:
                services.send_message(conv_bc, sender, body)
            self.stdout.write(self.style.SUCCESS("Seeded conversation: bob ↔ charlie"))
        else:
            self.stdout.write("bob ↔ charlie already has messages; skipped seeding.")

        # Seed Alice <-> Charlie conversation if empty.
        conv_ac = services.get_or_create_conversation(alice, charlie)
        if not conv_ac.messages.exists():
            for sender, body in [
                (alice, "Hi Charlie, just making sure everyone can chat."),
                (charlie, "Looks good! Messages render immediately."),
                (alice, "Sweet. This should help reviewers poke around."),
            ]:
                services.send_message(conv_ac, sender, body)
            self.stdout.write(self.style.SUCCESS("Seeded conversation: alice ↔ charlie"))
        else:
            self.stdout.write("alice ↔ charlie already has messages; skipped seeding.")

        self.stdout.write(self.style.SUCCESS("Seeding complete."))

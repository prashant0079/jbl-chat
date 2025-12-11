# jbl-chat

HTMX-enabled 1:1 chat built on Django with session auth and a simple signup flow.

## Quickstart (TL;DR)
```bash
POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_VIRTUALENVS_PATH=.venv poetry install
poetry run python jbl_chat/manage.py migrate
poetry run python jbl_chat/manage.py createsuperuser
poetry run python jbl_chat/manage.py runserver 8001
```
Visit: `/accounts/login/` (or `/accounts/signup/`), then `/users/`.

## Requirements
- Python ^3.9 (see `pyproject.toml`)
- Poetry 1.8.x (already used in this repo)

## Setup (exact steps)
1) Install dependencies (creates `.venv/` in project):
```bash
POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_VIRTUALENVS_PATH=.venv poetry install
```

2) Run migrations:
```bash
poetry run python jbl_chat/manage.py migrate
```

3) Create a superuser (for admin/login):
```bash
poetry run python jbl_chat/manage.py createsuperuser
```

4) Start the dev server (pick a free port, e.g. 8001):
```bash
poetry run python jbl_chat/manage.py runserver 8001
```

5) Log in and chat:
- Visit `/accounts/login/` (or `/accounts/signup/` to self-register), then `/users/` to start a conversation.

## Features
- Django session auth with login, logout, and signup (built-in `UserCreationForm`).
- 1:1 conversations only; enforced ordering + uniqueness + no self chat.
- Messaging with denormalized `last_message_at/last_message_id` for ordering.
- HTMX interactions: incremental polling (`/chat/<id>/poll/?after=`), OOB swaps for send form + message append, partial templates.
- Access control: only participants can view/poll/send; login required for chat views.
- UI: minimal dark theme, message bubbles, status dots, mobile-friendly layout.

## Key URLs
- `/accounts/login/` – login
- `/accounts/logout/` – logout
- `/accounts/signup/` – create account
- `/users/` – list users to start a chat
- `/chat/<user_id>/` – conversation detail
- `/chat/<user_id>/send/` – send message
- `/chat/<user_id>/poll/?after=<last_id>` – incremental polling

## Tests
```bash
poetry run python jbl_chat/manage.py test chat
```

## Seed sample data
Populate three demo users (alice, bob, charlie; password `password123`) and sample conversations:
```bash
poetry run python jbl_chat/manage.py seed_demo
```

Demo credentials (after seeding):
- alice / password123
- bob / password123
- charlie / password123

## Notes
- Uses HTMX via CDN for polling and out-of-band message updates.
- Session-based auth with Django’s built-in login/logout.
- Migrations included; `poetry.lock` committed for reproducible installs.
- (Optional) Add a short demo GIF if you want to showcase the flow.

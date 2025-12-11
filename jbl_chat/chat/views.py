from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MessageForm
from .services import (
    can_access_conversation,
    get_or_create_conversation,
    send_message,
)

User = get_user_model()


def signup(request):
    if request.user.is_authenticated:
        return redirect("chat:users_list")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("chat:users_list")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def users_list(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, "chat/users.html", {"users": users})


@login_required
def conversation_detail(request, user_id):
    other = get_object_or_404(User, id=user_id)
    if other == request.user:
        raise Http404("Cannot chat with yourself.")

    conversation = get_or_create_conversation(request.user, other)
    recent = conversation.messages.select_related("sender").order_by("-id")[:50]
    messages = list(recent)[::-1]
    form = MessageForm()
    context = {
        "conversation": conversation,
        "other": other,
        "messages": messages,
        "form": form,
    }
    return render(request, "chat/conversation.html", context)


@login_required
def send_message_view(request, user_id):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    other = get_object_or_404(User, id=user_id)
    try:
        conversation = get_or_create_conversation(request.user, other)
    except ValueError:
        raise Http404("Cannot chat with yourself.")

    if not can_access_conversation(conversation, request.user):
        raise Http404("No access to this conversation.")

    form = MessageForm(request.POST)
    if form.is_valid():
        message = send_message(conversation, request.user, form.cleaned_data["body"])
        if request.headers.get("HX-Request") == "true":
            return render(
                request,
                "chat/partials/send_response.html",
                {
                    "message": message,
                    "form": MessageForm(),
                    "other": other,
                },
            )
        return redirect("conversation_detail", user_id=other.id)

    if request.headers.get("HX-Request") == "true":
        return render(
            request,
            "chat/partials/message_form.html",
            {"form": form, "other": other},
            status=400,
        )
    return redirect("conversation_detail", user_id=other.id)


@login_required
def poll_messages(request, user_id):
    other = get_object_or_404(User, id=user_id)
    try:
        conversation = get_or_create_conversation(request.user, other)
    except ValueError:
        raise Http404("Cannot chat with yourself.")

    if not can_access_conversation(conversation, request.user):
        raise Http404("No access to this conversation.")

    after_param = request.GET.get("after")
    try:
        after_id = int(after_param) if after_param is not None else 0
    except (TypeError, ValueError):
        after_id = 0

    messages = (
        conversation.messages.select_related("sender")
        .filter(id__gt=after_id)
        .order_by("id")
    )
    if not messages.exists():
        return HttpResponse("")

    return render(
        request,
        "chat/partials/messages_incremental.html",
        {"messages": messages},
    )

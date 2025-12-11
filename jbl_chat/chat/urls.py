from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("users/", views.users_list, name="users_list"),
    path("chat/<int:user_id>/", views.conversation_detail, name="conversation_detail"),
    path("chat/<int:user_id>/send/", views.send_message_view, name="send_message"),
    path("chat/<int:user_id>/poll/", views.poll_messages, name="poll_messages"),
    path("accounts/signup/", views.signup, name="signup"),
]

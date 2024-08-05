from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    path("user/login", obtain_auth_token),
    path("user/contacts", views.ContactList.as_view()),
    path("user/contacts/<int:pk>", views.ContactDetail.as_view()),
]

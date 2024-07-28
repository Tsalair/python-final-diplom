from rest_framework.authtoken import views
from django.urls import path

urlpatterns = [
    path("user/login", views.obtain_auth_token),
]

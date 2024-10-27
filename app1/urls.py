from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

from .views import (main, register, logout_user)
urlpatterns = [
    path('', views.main, name='main'),
    path("accounts/login/", LoginView.as_view(template_name="app1/login.html"),
        name="login"),
    path("logout/", LogoutView.as_view(template_name="app1/logout.html"),
        name="logout"),
    path("register/", register, name="register"),
    path('UPLOAD', views.upload_document, name='upload_document'),
    path('summary', views.summarization, name='summary'),
]
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

from .views import (main, register, logout_user)
urlpatterns = [
    path('', views.main, name='main'),
    path("login/", LoginView.as_view(template_name="app1/login.html"),
        name="login"),
    path("logout/", LogoutView.as_view(template_name="app1/logout.html"),
        name="logout"),
    path("register/", register, name="register"),
    path('UPLOAD', views.upload_document, name='upload_document'),
    path('documents/<int:document_id>/original/', views.show_original, name='show_original'),
    path('documents/<int:document_id>/improve/', views.improve_document, name='improve_document'),
    path('documents/<int:document_id>/suggestions/', views.show_suggestions, name='show_suggestions'),
    path('documents/<int:document_id>/accept/', views.accept_improvements, name='accept_improvements'),
    path('documents/<int:document_id>/improved/', views.show_improved, name='show_improved'),
    path('documents/<int:document_id>/export/', views.export_pdf, name='export_pdf'),
    path('documents/', views.list_documents, name='list_documents'),
    path('documents/create/', views.create_document, name='create_document'),
    path('documents/<int:document_id>/', views.view_document, name='view_document'),
    path('documents/<int:document_id>/edit/', views.update_document, name='update_document'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
]
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Document, Content

UserModel = get_user_model()

class UserRegistrationForm(UserCreationForm):

    class Meta:
        model = UserModel
        fields = ["username", "password1", "password2"]



        
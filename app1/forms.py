from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Document, Content

UserModel = get_user_model()

class UserRegistrationForm(UserCreationForm):

    class Meta:
        model = UserModel
        fields = ["username", "password1", "password2"]

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['status'] 

class ContentForm(forms.ModelForm):
    original_text = forms.CharField(widget=forms.Textarea, required=True, label="Original Text")
    improved_text = forms.CharField(widget=forms.Textarea, required=False, label="Improved Text")

    class Meta:
        model = Content
        fields = ['original_text', 'improved_text']



        
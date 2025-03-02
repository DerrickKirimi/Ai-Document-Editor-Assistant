from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField

# Documents model to store metadata about each uploaded document.
class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('Uploaded', 'Uploaded'), ('Improved', 'Improved')])
    title = models.CharField(max_length=255, blank=True)  # New title field


    def __str__(self):
        return f"Document {self.id} by {self.user.username}"

# Content model to store original and improved text content.
class Content(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='content')
    original_text = RichTextField(null=True, blank=True)
    improved_text = RichTextField(null=True, blank=True)

    def __str__(self):
        return f"Content for Document {self.document.id}"

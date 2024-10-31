from django.contrib import admin
from .models import Document, Content

class ContentInline(admin.StackedInline):
    model = Content
    fields = ('original_text', 'improved_text')
    extra = 0  # No extra blank fields by default

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'upload_date', 'status', 'title')
    search_fields = ('user__username', 'status', 'title')
    list_filter = ('status', 'upload_date')
    ordering = ('-upload_date',)
    inlines = [ContentInline]  # Add the Content inline to Document admin

    # Specify editable fields
    fields = ('user', 'title', 'status')  # Only these fields will appear for editing in Document


from django.test import TestCase, Client
from django.urls import reverse
from .models import Document, Content, User

class DocumentViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create a sample user
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        # Create a sample document and content for testing
        self.document = Document.objects.create(user=self.user, status='draft')
        self.content = Content.objects.create(
            document=self.document,
            original_text="Original text content",
            improved_text="Improved text content"
        )

    def test_show_original_view(self):
        url = reverse('show_original', args=[self.document.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'document_assistant/showOriginal.html')
        self.assertContains(response, "Original text content")

    def test_show_suggestions_view(self):
        url = reverse('show_suggestions', args=[self.document.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'document_assistant/showSuggestions.html')
        self.assertContains(response, "Original text content")
        self.assertContains(response, "Improved text content")

    def test_show_improved_view(self):
        url = reverse('show_improved', args=[self.document.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'document_assistant/showImproved.html')
        self.assertContains(response, "Improved text content")

    def test_document_improvement_process(self):
        # Simulate uploading and improving the document
        url = reverse('improve_document', args=[self.document.id])
        response = self.client.post(url)
        
        # Check that improvement process succeeds (assuming improvement logic runs in the view)
        self.assertEqual(response.status_code, 302)  # Expecting a redirect after processing
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'Improved')  #  Status after improvement

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, HttpResponse
# For Flash Messages
from django.contrib import messages
import bleach

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


from .models import Document, Content
from django.utils import timezone
from .forms import UserRegistrationForm

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

import os
import docx2txt  # for DOCX files
from PyPDF2 import PdfReader  # for PDF files
from .models import Document, Content
from .forms import UserRegistrationForm, DocumentForm, ContentForm
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from weasyprint import HTML #To export pdf files

import re
import nltk
#nltk.download('punkt')
#nltk.download('stopwords')
#nltk.download('wordnet') 
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import heapq
from django.contrib import messages

import io
from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.http import JsonResponse


def register(request):
    """
    User Registration form
    Args:
        request (POST): New user registered
    """    
    form = UserRegistrationForm()
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserRegistrationForm()

    context = {"form": form}
    return render(request, "app1/register.html", context)

def logout_user(request):
    logout(request)
    return redirect("login")

@login_required
def main(request):
    return render(request, 'app1/base.html')

# Upload Document API
class UploadDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        uploaded_file = request.FILES.get('document')

        valid_extensions = ['.txt', '.doc', '.docx', '.pdf']
        _, file_extension = os.path.splitext(uploaded_file.name)

        if file_extension.lower() not in valid_extensions:
                messages.error(request, 'Invalid file format. Please upload a .pdf, .txt, .doc, or .docx file.')
                return render(request, 'app1/base.html')  # Stay on the upload page

            #Ensure the media directory exists
        os.makedirs('media', exist_ok=True)

            # Save the uploaded file to a temporary location
        temporary_file_path = os.path.join('media', uploaded_file.name)

        with open(temporary_file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

            # Set title based on filename without the extension
        title = os.path.splitext(uploaded_file.name)[0]
        text = ''

        # Determine file format and extract text accordingly
        if uploaded_file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                # DOCX file
            text = ''
            text = docx2txt.process(temporary_file_path)
        elif uploaded_file.content_type == 'application/pdf':
                # PDF file using PyPDF2
            reader = PdfReader(temporary_file_path)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
        elif uploaded_file.content_type == 'text/plain':
                # TXT file
            with open(temporary_file_path, 'r') as f:
                text = f.read()
        else:
            os.remove(temporary_file_path)
            return Response({'error': 'Invalid file format. Please upload a .pdf, .txt, .doc, or .docx file.'},
                            status=status.HTTP_400_BAD_REQUEST)

            # Remove the temporary file
        os.remove(temporary_file_path)

        # Save document metadata in Documents table
        document = Document.objects.create(user=request.user, status="Uploaded")

            # Save extracted content
        Content.objects.create(document=document, original_text=text)

        return Response({'message': 'Document uploaded and text extracted successfully!',
                         'document_id': document.id}, status=status.HTTP_201_CREATED)

# View Original Document API
class ShowOriginalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        context = {
            'document': document,
            'original_text': document.content.original_text,
        }
        return render(request, 'app1/showOriginal.html', context)

    def post(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        document.content.original_text = request.POST.get('extracted_text', '')
        document.content.save()
        return redirect('show_suggestions', document_id=document.id)

# Improve Document API
class ImproveDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        article_text = request.POST.get('extracted_text', '')

        model_type = os.getenv('IMPROVE_MODEL', 'nltk')
        
        if model_type == 'nltk':
            improved_text = improve_nltk(article_text)
        elif model_type == 't5':
            improved_text = improve_t5(article_text)
        else:
            return Response({'error': 'Invalid model type specified.'}, status=status.HTTP_400_BAD_REQUEST)

        document.content.improved_text = improved_text
        document.content.save()

        document.status = 'Improved'
        document.save()

        return Response({'message': 'Improvements Generated Successfully!'}, status=status.HTTP_200_OK)

# Show Suggestions API
class ShowSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        context = {
            'document': document,
            'original_text': document.content.original_text,
            'improved_text': document.content.improved_text,
        }
        return render(request, 'app1/showSuggestions.html', context)

    def post(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        improved_text = request.POST.get('improved_text', '')
        document.content.improved_text = improved_text
        document.content.save()
        return redirect('show_improved', document_id=document.id)

# Accept Improvements API
class AcceptImprovementsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        original_text = request.POST.get('original_text')
        improved_text = request.POST.get('improved_text')

        content = document.content
        content.original_text = original_text
        content.improved_text = improved_text
        content.save()

        document.status = "Accepted"
        document.save()

        return Response({'message': "Improvements have been accepted and saved successfully!"}, status=status.HTTP_200_OK)

# Show Improved Document API
class ShowImprovedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        context = {
            'document': document,
            'improved_text': document.content.improved_text,
        }
        return render(request, 'app1/showImproved.html', context)

    def post(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        final_improved_text = request.POST.get('final_improved_text', '')
        document.content.improved_text = final_improved_text
        document.content.save()

        if request.is_ajax():
            return JsonResponse({'success': True, 'message': 'Changes saved successfully.'})

        return redirect('show_improved', document_id=document.id)

# Export PDF API
class ExportPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        html_content = document.content.improved_text

        soup = BeautifulSoup(html_content, 'html.parser')

        for tag in soup.find_all():
            for attr in ["class", "style"]:
                if attr in tag.attrs:
                    del tag[attr]

        for br in soup.find_all('br'):
            br.insert_before('\n')

        cleaned_html = soup.prettify()

        context = {
            'improved_text': cleaned_html,
            'document': document,
        }
        html_string = render_to_string('app1/pdf_template.html', context)

        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{document.id}_improved.pdf"'
        return response

# List Documents API
class ListDocumentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        documents = Document.objects.filter(user=request.user).order_by('-upload_date')
        paginator = Paginator(documents, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'app1/list_documents.html', {'page_obj': page_obj})

# Document creation and update views will remain unchanged, or you can adapt them similarly


def create_document(request):
    if request.method == 'POST':
        document_form = DocumentForm(request.POST)
        content_form = ContentForm(request.POST)
        
        if document_form.is_valid() and content_form.is_valid():
            document = document_form.save(commit=False)
            document.user = request.user  # Assuming Document has a foreign key to User
            document.save()

            content = content_form.save(commit=False)
            content.document = document
            content.save()

            messages.success(request, 'Document created successfully.')
            return redirect('list_documents')
    else:
        document_form = DocumentForm()
        content_form = ContentForm()

    return render(request, 'app1/create_document.html', {
        'document_form': document_form,
        'content_form': content_form
    })

@login_required
def update_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    content = get_object_or_404(Content, document=document)
    
    if request.method == 'POST':
        document_form = DocumentForm(request.POST, instance=document)
        content_form = ContentForm(request.POST, instance=content)
        if document_form.is_valid() and content_form.is_valid():
            document_form.save()
            content_form.save()
            messages.success(request, 'Document updated successfully.')
            return redirect('list_documents')
    else:
        document_form = DocumentForm(instance=document)
        content_form = ContentForm(instance=content)
    return render(request, 'app1/update_document.html', {
        'document_form': document_form, 'content_form': content_form, 'document': document
    })

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully.')
        return redirect('list_documents')
    return render(request, 'app1/delete_document.html', {'document': document})

@login_required
def view_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    content = document.content
    return render(request, 'app1/view_document.html', {'document': document, 'content': content})

def improve_nltk(article_text):
    # Preprocessing
    article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
    article_text = re.sub(r'\s+', ' ', article_text)
    formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text)
    formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)
    sentence_list = nltk.sent_tokenize(article_text)
    stopwords = nltk.corpus.stopwords.words('english')

    # Word frequency and scoring sentences
    word_frequencies = {}
    for word in nltk.word_tokenize(formatted_article_text):
        if word not in stopwords:
            word_frequencies[word] = word_frequencies.get(word, 0) + 1
    maximum_frequency = max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word] /= maximum_frequency

    sentence_scores = {}
    for sent in sentence_list:
        for word in nltk.word_tokenize(sent.lower()):
            if word in word_frequencies and len(sent.split()) < 30:
                sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word]
                
    summary_sentences = heapq.nlargest(7, sentence_scores, key=sentence_scores.get)
    return ' '.join(summary_sentences)

def improve_t5(text):
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    # Load T5 model and tokenizer once when the module is imported
    model_name = "t5-small"
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    input_text = f"paraphrase: {text} </s>"
    inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    
    outputs = model.generate(
        inputs,
        max_length=100,
        num_return_sequences=1,
        num_beams=5,
        early_stopping=True
    )
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
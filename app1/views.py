from django.shortcuts import render, redirect, HttpResponse
# For Flash Messages
from django.contrib import messages

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

import re
import nltk
#nltk.download('punkt')
#nltk.download('stopwords')
#nltk.download('wordnet') 
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import heapq

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
    return render(request,'app1/base.html')

global text
def upload_document(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES['document']

            valid_extensions = ['.txt', '.doc', '.docx', '.pdf']  # Add valid formats
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
                messages.error(request, 'Invalid file format. Please upload a .txt, .doc, or .docx file.')
                return render(request, 'app1/base.html')  # Stay on the upload page

            # Remove the temporary file
            os.remove(temporary_file_path)

            # Save document metadata in Documents table
            document = Document.objects.create(user=request.user, status="Uploaded")

            # Save extracted content
            Content.objects.create(document=document, original_text=text)

            messages.success(request, "Document uploaded and text extracted successfully !")

            return redirect('show_original', document_id=document.id)
            
            #return render(request, 'app1/showOriginal.html', {'extracted_text': text})

    except Exception as e:
        # Handle exceptions (e.g., file not found, extraction error)
        messages.error(request, 'Incorrect File Format: {}'.format(str(e)))
    return render(request, 'app1/showOriginal.html')

@login_required
def show_original(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    context = {
        'document': document,
        'original_text': document.content.original_text,
    }

    return render(request, 'app1/showOriginal.html', context)

def improve_document(request, document_id):
    if request.method == 'POST':
        # Get the article text from the form data
        article_text = request.POST.get('extracted_text', '')

        document = get_object_or_404(Document, id=document_id, user=request.user)
        original_text = document.content.original_text

        # Preprocessing steps

        # Removing Square Brackets and Extra Spaces
        article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
        article_text = re.sub(r'\s+', ' ', article_text)
        # Removing special characters and digits
        formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text )
        formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)
        sentence_list = nltk.sent_tokenize(article_text)
        stopwords = nltk.corpus.stopwords.words('english')

        word_frequencies = {}
        for word in nltk.word_tokenize(formatted_article_text):
            if word not in stopwords:
                if word not in word_frequencies.keys():
                    word_frequencies[word] = 1
                else:
                    word_frequencies[word] += 1
            maximum_frequncy = max(word_frequencies.values())
        for word in word_frequencies.keys():
            word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)
            sentence_scores = {}
        for sent in sentence_list:
            for word in nltk.word_tokenize(sent.lower()):
                if word in word_frequencies.keys():
                    if len(sent.split(' ')) < 30:
                        if sent not in sentence_scores.keys():
                            sentence_scores[sent] = word_frequencies[word]
                        else:
                            sentence_scores[sent] += word_frequencies[word]
        import heapq
        summary_sentences = heapq.nlargest(7, sentence_scores, key=sentence_scores.get)

        summary = ' '.join(summary_sentences)
        output_text = re.sub(r'\W', ' ', str(summary))

        # Update the document with improved text
        document.content.improved_text = summary
        document.content.save()
        document.status = 'Improved'
        document.save()

        messages.success(request, 'Improvements Generated Successfully !')

        # Passing both original_text and improved_text. Note both first and second argument are determined within this function
        return redirect('show_suggestions', document_id=document.id)
    return render(request, 'base.html')


@login_required
def show_suggestions(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    context = {
        'document': document,
        'original_text': document.content.original_text,
        'improved_text': document.content.improved_text,
    }
    return render(request, 'app1/showSuggestions.html', context)

@login_required
def accept_improvements(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)

    if request.method == 'POST':
        original_text = request.POST.get('original_text')
        improved_text = request.POST.get('improved_text')

        # Update the content model
        content = document.content
        content.original_text = original_text
        content.improved_text = improved_text
        content.save()  # Save changes

        # Update document status if necessary
        document.status = "Accepted"
        document.save()

        messages.success(request, "Improvements have been accepted and saved successfully!")
        return redirect('show_original', document_id=document.id)

    # Handle GET requests if necessary
    context = {
        'original_text': document.content.original_text,
        'improved_text': document.content.improved_text,
        'document': document,
    }

    return render(request, 'app1/showSuggestions.html', context)
from django.shortcuts import render, redirect, HttpResponse
# For Flash Messages
from django.contrib import messages
import bleach

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
    
    if request.method == 'POST':
        # Save the edited original text from CKEditor
        document.content.original_text = request.POST.get('extracted_text', '')
        document.content.save()

        # Redirect to show_suggestions after saving the original text
        return redirect('show_suggestions', document_id=document.id)
        
        # Optionally, add a success message
        messages.success(request, 'Document updated successfully!')

    # Prepare context with the current original text
    context = {
        'document': document,
        'original_text': document.content.original_text,  # Ensure you're pulling the latest saved text
    }
    return render(request, 'app1/showOriginal.html', context)

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

@login_required
def improve_document(request, document_id):
    # Retrieve the document based on the provided ID
    document = get_object_or_404(Document, id=document_id, user=request.user)

    if request.method == 'POST':
        article_text = request.POST.get('extracted_text', '')

        model_type = os.getenv('IMPROVE_MODEL', 'nltk')

        # Determine which model to use for improvement
        if model_type == 'nltk':
            improved_text = improve_nltk(article_text)
        elif model_type == 't5':
            improved_text = improve_t5(article_text)
        else:
            messages.error(request, 'Invalid model type specified.')
            return redirect('home')

        # Save the improved text to the document's content
        document.content.improved_text = improved_text
        document.content.save()

        # Update the document status
        document.status = 'Improved'
        document.save()

        messages.success(request, 'Improvements Generated Successfully!')
        return redirect('show_suggestions', document_id=document.id)

    # If GET request, return the original text for rendering
    return render(request, 'app1/showOriginal.html', {
        'document': document,
        'original_text': document.content.original_text,  # Ensure original text is available
        'messages': messages.get_messages(request),  # Pass messages for notification
    })

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
        return redirect('show_improved', document_id=document.id)

    # Handle GET requests if necessary
    context = {
        'original_text': document.content.original_text,
        'improved_text': document.content.improved_text,
        'document': document,
    }

    return render(request, 'app1/showSuggestions.html', context)

@login_required
def show_improved(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    # Fetch the improved text from the content model
    context = {
        'improved_text': document.content.improved_text,  
        'document': document,
    }

    return render(request, 'app1/showImproved.html', context)

def clean_html(html):
    return bleach.clean(html, strip=True)

@login_required
def export_pdf(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)

    # Clean the improved text
    cleaned_text = clean_html(document.content.improved_text)

    # Render the HTML for the PDF
    context = {
        'improved_text': cleaned_text,
        'document': document,
    }
    html_string = render_to_string('app1/pdf_template.html', context)

    # Generate PDF
    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{document.id}_improved.pdf"'
    return response
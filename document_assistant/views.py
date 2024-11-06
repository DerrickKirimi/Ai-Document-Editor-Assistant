from django.shortcuts import render, redirect, HttpResponse
import requests
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
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

import io
from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.http import JsonResponse

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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
    return render(request, "document_assistant/register.html", context)

def logout_user(request):
    logout(request)
    return redirect("login")

@login_required
def main(request):
    return render(request,'document_assistant/base.html')

global text
def upload_document(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES['document']

            valid_extensions = ['.txt', '.doc', '.docx', '.pdf']  # Add valid formats
            _, file_extension = os.path.splitext(uploaded_file.name)

            if file_extension.lower() not in valid_extensions:
                messages.error(request, 'Invalid file format. Please upload a .pdf, .txt, .doc, or .docx file.')
                return render(request, 'document_assistant/base.html')  # Stay on the upload page

            #Ensure the media directory exists
            os.makedirs('media', exist_ok=True)

            # Save the uploaded file to a temporary location
            temporary_file_path = os.path.join('media', uploaded_file.name)
            with open(temporary_file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Set title based on filename without the extension
            title = os.path.splitext(uploaded_file.name)[0]

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
                return render(request, 'document_assistant/base.html')  # Stay on the upload page

            # Remove the temporary file
            os.remove(temporary_file_path)

            # Save document metadata in Documents table
            document = Document.objects.create(user=request.user, title=title, status="Uploaded")

            # Save extracted content
            Content.objects.create(document=document, original_text=text)

            messages.success(request, "Document uploaded and text extracted successfully !")

            return redirect('show_original', document_id=document.id)
            
            #return render(request, 'document_assistant/showOriginal.html', {'extracted_text': text})

    except Exception as e:
        # Handle exceptions (e.g., file not found, extraction error)
        messages.error(request, 'Incorrect File Format: {}'.format(str(e)))
    return render(request, 'document_assistant/showOriginal.html')

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
    return render(request, 'document_assistant/showOriginal.html', context)

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
                
    summary_sentences = heapq.nlargest(300, sentence_scores, key=sentence_scores.get)
    return ' '.join(summary_sentences)



def improve_grok(article_text):
    # Define the API endpoint and headers
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",  # Use the API key from environment variable
    }

    # Prepare the payload with the prompt
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional document editor creating a clear, structured plain text output. "
                    "Format the document for optimal readability: separate content into paragraphs with line breaks, "
                    "use plain hyphens (-) for bullet points, and ensure each heading appears on its own line. "
                    "Place each bullet point and each paragraph on a new line, and split long lines as needed for readability. "
                    "Avoid any markdown symbols, bold markers (**), or special characters; use only plain text."
    
                )
            },
            {
                "role": "user",
                "content": (
                    f"Please improve the following document for clarity and professional structure. "
                    f"Format the document in plain text with clear headings, paragraphs, and line breaks "
                    f"for readability. Do not use markdown symbols. Here is the document:\n\n{article_text}"
                )
            }
        ],
        "model": "grok-beta",
        "stream": False,
        "temperature": 0
    }

    # Make the API request
    response = requests.post(url, headers=headers, json=payload)

    # Handle the response
    if response.status_code == 200:
        response_data = response.json()
        # Extract the improved text from the response
        improved_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return improved_text.strip()  # Return the improved text
    else:
        # Handle errors
        print(f"Error: {response.status_code}, {response.text}")
        return "Error improving the document."

def improve_t5(text):
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    # Load T5 model and tokenizer once the module is imported
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
    # Retrieve the document based on the provided ID and the requesting user
    document = get_object_or_404(Document, id=document_id, user=request.user)

    if request.method == 'POST':
        article_text = request.POST.get('extracted_text', '')
        model_type = os.getenv('IMPROVE_MODEL', 'nltk')  # Use environment variable for model choice

        # Select model and apply improvement based on the environment setting
        if model_type == 'nltk':
            improved_text = improve_nltk(article_text)
        elif model_type == 'grok':
            improved_text = improve_grok(article_text)
        elif model_type == 't5':
            improved_text = improve_t5(article_text)
        else:
            messages.error(request, 'Invalid model type specified.')
            return redirect('home')

        # Save the improved text and update document status
        document.content.improved_text = improved_text
        document.content.save()
        document.status = 'Improved'
        document.save()

        # Success message and redirect to show suggestions
        messages.success(request, 'Improvements Generated Successfully!')
        return redirect('show_suggestions', document_id=document.id)

    # If GET request, return the original text for rendering
    return render(request, 'document_assistant/showOriginal.html', {
        'document': document,
        'original_text': document.content.original_text,  # Ensure original text is available
        'messages': messages.get_messages(request),  # Pass messages for notification
    })

@login_required
def show_suggestions(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)

    if request.method == 'POST':
        # Capture the improved text from the CKEditor field
        improved_text = request.POST.get('improved_text', '')
        document.content.improved_text = improved_text  # Save the improved text
        document.content.save()  # Save the improved text to the Document
        return redirect('show_improved', document_id=document.id)  # Redirect to improved view

    context = {
        'document': document,
        'original_text': document.content.original_text,  # Access original text
        'improved_text': document.content.improved_text,  # Access improved text
    }
    return render(request, 'document_assistant/showSuggestions.html', context)


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

    return render(request, 'document_assistant/showSuggestions.html', context)

@login_required
def show_improved(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)

    if request.method == 'POST':
        # Capture the final improved text from the CKEditor field
        final_improved_text = request.POST.get('final_improved_text', '')
        document.content.improved_text = final_improved_text  # Save the final improved text
        document.content.save()  # Save changes to the Document
        
        # Check if it's an AJAX request
        if request.is_ajax():
            return JsonResponse({'success': True, 'message': 'Changes saved successfully.'})

        return redirect('show_improved', document_id=document.id)  # Redirect back to showImproved with updated text

    context = {
        'document': document,
        'improved_text': document.content.improved_text,  # Display the improved text
    }
    return render(request, 'document_assistant/showImproved.html', context)


def clean_html(html):
    return bleach.clean(html, strip=True)

@login_required
def export_pdf(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)

    # Get the HTML content from the improved text
    html_content = document.content.improved_text

    # Use BeautifulSoup to clean and modify the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Optional: Clean specific tags, remove unwanted attributes, or modify structure
    for tag in soup.find_all():
        # Example: Strip unwanted attributes like class and style
        for attr in ["class", "style"]:
            if attr in tag.attrs:
                del tag[attr]

    # Maintain new lines by replacing <br> tags and ensuring paragraph tags are used
    for br in soup.find_all('br'):
        br.insert_before('\n')  # Insert a new line before <br> tags

    # Convert back to a string while keeping the text formatted properly
    cleaned_html = soup.prettify()  # Use prettify for structured HTML

    # Render the HTML for the PDF
    context = {
        'improved_text': cleaned_html,  # Use cleaned HTML for rendering
        'document': document,
    }
    html_string = render_to_string('document_assistant/pdf_template.html', context)

    # Generate PDF
    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{document.id}_improved.pdf"'
    return response

from .forms import DocumentForm, ContentForm

@login_required
def list_documents(request):
    documents = Document.objects.filter(user=request.user).order_by('-upload_date')
    paginator = Paginator(documents, 5)  # Show 5 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'document_assistant/list_documents.html', {'page_obj': page_obj})


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

    return render(request, 'document_assistant/create_document.html', {
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
    return render(request, 'document_assistant/update_document.html', {
        'document_form': document_form, 'content_form': content_form, 'document': document
    })

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully.')
        return redirect('list_documents')
    return render(request, 'document_assistant/delete_document.html', {'document': document})

@login_required
def view_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    content = document.content
    return render(request, 'document_assistant/view_document.html', {'document': document, 'content': content})


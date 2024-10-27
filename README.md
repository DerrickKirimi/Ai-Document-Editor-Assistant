# DocSummarizationTool

# Automatic Text Summarization Web Application

This Django-based web application is designed to perform automatic text summarization on various document formats, including DOCX, PDF, and plain text files. The summarized text can be generated after uploading a document, and the application supports flash messages for user feedback.

## Features

- Supports DOCX, PDF, and plain text file formats
- Flash messages for user feedback
- Automatic text summarization using nltk and heapq libraries

# Getting Started

## Clone the repository:

git clone https://github.com/nassrkhan/Automatic-Text-Summarization-Web-Application.git

## Navigate to the project directory:

cd document-summarization

## Run the Django development server:

python manage.py runserver
Open your web browser and visit http://localhost:8000/ to access the application.

Upload a document on the main page to extract text and view the summary on the following page.

# File Structure

summarization/views.py: Contains Django views for document upload and text summarization.
media/: Temporary storage for uploaded files.
templates/: HTML templates for rendering pages.

# Acknowledgements

Django
nltk
docx2txt
PyPDF2

## Prerequisites

Make sure you have the following installed:

- Python 3.x
- Django
- nltk (Natural Language Toolkit)
- docx2txt
- PyPDF2

You can install the required Python packages using:

```bash
pip install django nltk docx2txt PyPDF2
python -m nltk.downloader punkt stopwords wordnet


```

django-admin startproject projectname projectdir

python manage.py startapp appname

add models

add 'appname.apps.AppnameConfig' to settings.py

python manage.py makemigrations app1
python manage.py sqlmigrate app1 0001

python manage.py migrate



python manage.py sqlmigrate app1 0001
BEGIN;
------

-- Create model Document
------------------------

CREATE TABLE "app1_document" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "upload_date" datetime NOT NULL, "status" varchar(20) NOT NULL, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

-- Create model Content
-----------------------

CREATE TABLE "app1_content" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "original_text" text NOT NULL, "improved_text" text NULL, "document_id" bigint NOT NULL UNIQUE REFERENCES "app1_document" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "app1_document_user_id_de3be396" ON "app1_document" ("user_id");
COMMIT;
First include this in your settings.py CRISPY_TEMPLATE_PACK = 'bootstrap4'
After doing that you might encounter a challenge that the template does not exist. If that occurs, make sure you have crispy-bootstrap installed - pip install crispy-bootstrap4 and add 'crispy_bootstrap4' to your list of INSTALLED_APPS.

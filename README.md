# Document Assistant

Document Assistant is an AI-powered web application designed to help users edit, improve, and export their documents. The application offers a friendly user interface for document upload and editing, backed by natural language processing (NLP) capabilities. Users can view suggestions for document improvements, accept or reject changes, and export their final document as a PDF.

## Table of Contents

- [Document Assistant](#document_assistant)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Technologies](#technologies)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Endpoints](#endpoints)

## Features

- **User Authentication**: Register, login, and logout functionality.
- **Document Upload**: Upload documents for processing.
- **NLP-Powered Improvements**: Apply NLP models (spaCy or Hugging Face) to suggest document enhancements.
- **Side-by-Side Editing**: View and edit the original and improved documents side-by-side with CKEditor.
- **Accept/Reject Suggestions**: Accept improvements or revert to original text.
- **PDF Export**: Export the improved document to PDF.

## Technologies

- **Frontend**: HTML, CSS, JavaScript, CKEditor for editing interface
- **Backend**: Python, Django
- **NLP Models**: spaCy (default) or Hugging Face (optional via command-line argument)

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/DerrickKirimi/Ai-Document-Editor-Assistant.git
   cd Ai-Document-Editor-Assistant
   ```
2. **Create a virtual environment**:

```bash
python3 -m venv env
source env/bin/activate  # For Linux/macOS
env\Scripts\activate     # For Windows
```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
   **Configure Environment Variables**:

    Create a .env file in the root directory if it doesn’t exist.

    Add your API key to the .env file as follows:

    ```bash
    XAI_API_KEY=your_api_key_here
    ```

4. **Setup Database**:

```bash
python manage.py migrate
```

5.**Create a superuser**:

```bash
python manage.py createsuperuser
```

6.**Run the server**:

```bash
python manage.py runserver          #Defaults to nltk model
```

**Run with Model Options**:

To specify the model options, use the following arguments when starting the server:

```bash
python manage.py runserver --model nltk    # Use NLTK for document improvements
python manage.py runserver --model grok    # Use Grok2 via X.ai api key
python manage.py runserver --model hg      # Use HuggingFace transformers T5 model 

```

## Usage

- Login: Start by logging into the application (or register if you are a new user).
- Upload a Document: Navigate to the Upload page and upload a document.
- View and Edit: Review the original and suggested improvements in the side-by-side editor.
- Accept/Reject Changes: Choose which improvements to keep.
- Export: Download your improved document as a PDF.

## Endpoints

- / GET Home page
- /login/ GET Login page
- /logout/ GET Logout page
- /register/ GET Registration page
- /UPLOAD POST Upload a new document
- /documents/`<id>`/original/ GET View the original document
- /documents/`<id>`/improve/ POST Improve document using NLP
- /documents/`<id>`/suggestions/ GET View improvement suggestions
- /documents/`<id>`/accept/ POST Accept suggested improvements
- /documents/`<id>`/improved/ GET View the improved document
- /documents/`<id>`/export/ GET Export the improved document as a PDF
- /documents/ GET List all uploaded documents
- /documents/create/ POST Create a new document entry
- /documents/`<id>`/ GET View details of a specific document
- /documents/`<id>`/edit/ PUT Edit a specific document
- /documents/`<id>`/delete/ DELETE Delete a specific document

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from dotenv import load_dotenv  # Import to load environment variables from .env

def main():
    """Run administrative tasks."""
    load_dotenv()  # Load environment variables from .env, if available
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
    
    # Set default model type and check if --model argument is provided
    model_type = os.getenv('IMPROVE_MODEL', 'nltk')  # Use .env value or default to 'nltk'
    if '--model' in sys.argv:
        model_index = sys.argv.index('--model') + 1
        if model_index < len(sys.argv):
            model_type = sys.argv[model_index]
            # Remove --model and its value from sys.argv to avoid interfering with Django commands
            sys.argv.pop(model_index)  
            sys.argv.remove('--model')
    
    # Set IMPROVE_MODEL in environment
    os.environ['IMPROVE_MODEL'] = model_type
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

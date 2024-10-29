#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
    
    # Check for the model argument
    model_type = 'nltk'  # default
    if '--model' in sys.argv:
        model_index = sys.argv.index('--model') + 1
        if model_index < len(sys.argv):
            model_type = sys.argv[model_index]
            sys.argv.remove('--model')
            sys.argv.remove(model_type)

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

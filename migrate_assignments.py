#!/usr/bin/env python
import os
import sys
import django

# Add the crm_lms directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crm_lms'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Apply migration
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate', 'assignments'])

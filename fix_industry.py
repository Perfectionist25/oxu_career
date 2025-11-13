import os
import django
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import EmployerProfile
from jobs.models import Industry

# Get the invalid industry names
invalid_names = ['Soha haqida ma`lumot', '']

# Find the industry IDs that match these names
invalid_industry_ids = Industry.objects.filter(name__in=invalid_names).values_list('id', flat=True)

print(f"Invalid industry IDs: {list(invalid_industry_ids)}")

# Update employer profiles with these industry IDs to NULL
updated_count = EmployerProfile.objects.filter(industry__in=invalid_industry_ids).update(industry=None)

print(f"Updated {updated_count} employer profiles")

# Verify the update
remaining_invalid = EmployerProfile.objects.filter(industry__in=invalid_industry_ids).count()
print(f"Remaining profiles with invalid industry: {remaining_invalid}")

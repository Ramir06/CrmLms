import os
import django

# Устанавливаем путь к Django проекту
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.finance.models import FinanceCategory
from apps.organizations.models import Organization

print('Все категории в базе:')
for cat in FinanceCategory.objects.all().order_by('name'):
    org_name = cat.organization.name if cat.organization else 'Без организации'
    print(f'  {cat.name} - {org_name}')

print('\nКатегории по организациям:')
for org in Organization.objects.all():
    cats = FinanceCategory.objects.filter(organization=org).order_by('name')
    print(f'{org.name}: {cats.count()} категорий')
    for cat in cats:
        print(f'  - {cat.name}')

print('\nДубликаты категорий:')
from collections import defaultdict
category_orgs = defaultdict(list)
for cat in FinanceCategory.objects.all():
    category_orgs[cat.name].append(cat.organization.name if cat.organization else 'Без организации')

for name, orgs in category_orgs.items():
    if len(orgs) > 1:
        print(f'{name}: {orgs}')

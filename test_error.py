import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as_project.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth.models import User

u = User.objects.first()
c = Client(raise_request_exception=True)
c.force_login(u)

try:
    c.get('/inventory/as_app/company/')
except Exception as getattr_e:
    import traceback
    with open('error_trace.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)

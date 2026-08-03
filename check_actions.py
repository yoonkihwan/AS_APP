import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'as_project.settings'
django.setup()

from django.contrib.admin.sites import AdminSite
from as_app.admin import StatusRegistrationAdmin
from as_app.models import StatusRegistration

adm = StatusRegistrationAdmin(StatusRegistration, AdminSite())

# Check what actions are registered
from django.http import HttpRequest
from django.contrib.auth.models import User

# Create a mock request
request = HttpRequest()
request.user = User.objects.filter(is_superuser=True).first()

actions = adm.get_actions(request)
print(f"Number of actions: {len(actions)}")
print()
for key, (func, name, desc) in actions.items():
    func_name = getattr(func, '__name__', str(func))
    original_name = getattr(func, 'original_function_name', 'N/A')
    print(f"  key='{key}', func_name='{func_name}', original='{original_name}', desc='{desc}'")

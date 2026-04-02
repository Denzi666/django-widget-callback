import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings') # Проверь, что твой проект называется mysite
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = 'admin'
email = 'klychkov_s.66@mail.ru'  # <-- Впиши сюда свою почту
password = '222'          # <-- Впиши сюда свой пароль

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Суперпользователь успешно создан!")
else:
    print("Суперпользователь уже существует.")
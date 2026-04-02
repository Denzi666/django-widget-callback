import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings') 
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print("Суперпользователь успешно создан!")
    else:
        print("Суперпользователь уже существует.")
else:
    print("Ошибка: Переменная DJANGO_SUPERUSER_PASSWORD не найдена в системе.")
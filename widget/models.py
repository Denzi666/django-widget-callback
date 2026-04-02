from django.db import models

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название компании")
    api_key = models.CharField(max_length=100, unique=True, verbose_name="Уникальный API ключ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    ai_prompt = models.TextField(
        verbose_name="Инструкция для ИИ(Промпт)",
        blank=True,
        null=True,
        help_text="Здесь напиши роль бота и правила общения для этой компании."
    )
   
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

class Callback(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='callbacks',
        verbose_name='Компания',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    message = models.TextField()

    ai_response = models.TextField(verbose_name="Ответ ИИ", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__ (self):
        return f"Заявка от {self.name}"
    
    class Meta:
        verbose_name = "Обратный звонок"
        verbose_name_plural = "Обратные звонки"

from django.db import models

# Create your models here.
class Callback(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__ (self):
        return f"Заявка от {self.name}"
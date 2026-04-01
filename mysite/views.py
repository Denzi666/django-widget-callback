import requests
import environ
from django.db import models
from django.shortcuts import redirect, render
from widget.models import Callback
from django.contrib.auth.decorators import login_required

env = environ.Env()
environ.Env.read_env()

def home_page(request):
    if request.method == "POST":
        v_name = request.POST.get("client_name")
        v_phone = request.POST.get("client_phone")
        v_message = request.POST.get("client_message")

        Callback.objects.create(name=v_name, phone=v_phone, message=v_message)

        text_for_tg = (
            f"Новая заявка!\nИмя: {v_name}\nТелефон: {v_phone}\n Сообщение: {v_message}"
        )
        send_telegram_message(text_for_tg)

        return redirect("thanks_page")
    return render(request, "index.html")

def thanks_page(request):
    return render(request, "thanks.html")

@login_required
def requests_list(request):
     v_all_requests = Callback.objects.all()
     return render(request, "list.html", {"requests": v_all_requests})

def send_telegram_message(message_text):
    token = env("TELEGRAM_TOKEN")
    chat_id = env("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {"chat_id": chat_id, "text": message_text}

    try:
        requests.post(url, data=payload)
    except:
        pass    


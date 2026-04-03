import requests
import environ
import json
import re

from openai import OpenAI
from django.db import models
from django.shortcuts import redirect, render
from widget.models import Callback, Company
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

env = environ.Env()
environ.Env.read_env()

def ask_ai(prompt, user_message):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=env("OPENROUTER_API_KEY") 
    )

    try:
        # Используем метод, который выдает ответ здесь и сейчас
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                # Отдаем инструкцию компании (Промпт)
                {"role": "system", "content": prompt}, 
                # Отдаем сообщение живого клиента с сайта
                {"role": "user", "content": user_message} 
            ],
            max_tokens=500,  # Защита от слишком длинных и дорогих ответов
            temperature=0.7  # Оптимальный баланс между строгостью и креативностью
        )
        
        # Забираем из ответа только сгенерированный текст
        return response.choices[0].message.content
        
    except Exception as e:
        # Если что-то пойдет не так (например, на балансе нет денег), мы увидим ошибку
        return f"Ошибка ИИ: {str(e)}"

def home_page(request):
    if request.method == "POST":
        v_name = request.POST.get("client_name")
        v_phone = request.POST.get("client_phone")
        v_message = request.POST.get("client_message")

        # 1. Забираем API-ключ из формы
        v_api_key = request.POST.get("company_api_key")

        # 2. Ищем компанию по ключу в базе данных
        v_company = None
        if v_api_key:
            v_company = Company.objects.filter(api_key=v_api_key).first()

        ai_reply = ""

        if v_company and v_company.ai_prompt:
            ai_reply = ask_ai(v_company.ai_prompt, v_message)
        
        # 3. Создаем заявку и ПРИВЯЗЫВАЕМ компанию
        Callback.objects.create(
            name=v_name,
            phone=v_phone, 
            message=v_message,
            company = v_company,
            ai_response=ai_reply
            )

        # 1. Базовый текст заявки
        text_for_tg = (
            f"Новая заявка!\nИмя: {v_name}\nТелефон: {v_phone}\nСообщение: {v_message}"
        )
        
        # 2. Добавляем компанию, если она определилась
        if v_company:
            text_for_tg += f"\nКомпания: {v_company.name}"
            
        # 3. ИИ ответ (Добавляем .strip(), чтобы убрать пустые невидимые строки в начале и конце)
        ai_reply = ai_reply.strip()
        
        if ai_reply:
            text_for_tg += f"\n\n🤖 Ответ ИИ:\n{ai_reply}"
        else:
            # Теперь мы точно увидим, если ИИ промолчал!
            text_for_tg += f"\n\n🤖 Ответ ИИ: ❌ Ошибка или пустой ответ"

        # 4. И только теперь отправляем
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

@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            if not user_message:
                return JsonResponse({"error": "Сообщение пустое"}, status=400)
            
            phone_pattern = r'(?:\+7|8)?[-( ]*\d{3}[-) ]*\d{3}[- ]*\d{2}[- ]*\d{2}|\b\d{10}\b'
            phones = re.findall(phone_pattern, user_message)

            if phones:
                detected_phone = phones[0]

                # Сохраняем его в базу данных:
                Callback.objects.create(
                    name="Лид из Чата 🤖", 
                    phone=detected_phone, 
                    message=user_message
                )
    
                # Отправка номера в телеграм:
                send_telegram_message(f"🔥 Новый лид из чата!\nТелефон: {detected_phone}\nСообщение: {user_message}")

                print(f"ПЕРЕХВАЧЕН ТЕЛЕФОН: {detected_phone}")

            system_prompt = (
                "Ты — опытный менеджер по продажам автосалона 'Broom'. Твоя цель — помочь клиенту "
                "с выбором автомобиля и ОБЯЗАТЕЛЬНО мотивировать его оставить свой номер телефона "
                "для связи с менеджером или записи на тест-драйв. "
                "Общайся вежливо, используй смайлики. Если клиент задает вопрос о наличии, "
                "назови пару популярных моделей (например, Geely Coolray, Haval Jolion, Lada Vesta) "
                "и сразу спроси: 'На какой номер телефона я могу записать вас на тест-драйв, чтобы вы оценили авто лично?'"
            )

            ai_response = ask_ai(system_prompt, user_message)

            return JsonResponse({"reply": ai_response})
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status = 500)
        
    return JsonResponse({"error": "Только POST запросы!"}, status = 405)
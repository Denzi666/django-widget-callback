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

def ask_ai(messages_list):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=env("OPENROUTER_API_KEY") 
    )

    try:
        # Используем метод, который выдает ответ здесь и сейчас
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=messages_list,
            max_tokens=500,  # Защита от слишком длинных и дорогих ответов
            temperature=0.3  # Оптимальный баланс между строгостью и креативностью
        )
        
        # Забираем из ответа только сгенерированный текст
        return response.choices[0].message.content
        
    except Exception as e:
        # Если что-то пойдет не так (например, на балансе нет денег), мы увидим ошибку
        return f"Ошибка ИИ: {str(e)}"

def home_page(request):
    return render(request, "index.html")

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
            # ЗАБИРАЕМ API-КЛЮЧ, КОТОРЫЙ ПРИШЕЛ С ФРОНТЕНДА
            company_api_key = data.get("api_key", "")

            if not user_message:
                return JsonResponse({"error": "Сообщение пустое"}, status=400)
            
            # ПОИСК КОМПАНИИ В БАЗЕ ДАННЫХ
            v_company = None
            if company_api_key:
                v_company = Company.objects.filter(api_key=company_api_key).first()
            
            phone_pattern = r'(?:\+7|7|8)?[\s\-]?\(?[489]\d{2}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\b\d{10}\b'
            phones = re.findall(phone_pattern, user_message)

            if phones:
                detected_phone = phones[0]

                # ПРИВЯЗКА КОМПАНИИ К ЗАЯВКЕ
                Callback.objects.create(
                    name="Лид из Чата 🤖", 
                    phone=detected_phone, 
                    message=user_message,
                    company=v_company # связь с компанией
                )
    
                # УВЕДОМЛЕНИЕ В ТГ 
                tg_text = f"🔥 Новый лид из чата!\nТелефон: {detected_phone}\nСообщение: {user_message}"
                if v_company:
                    tg_text += f"\nКомпания: {v_company.name}"
                
                send_telegram_message(tg_text)

                print(f"ПЕРЕХВАЧЕН ТЕЛЕФОН: {detected_phone}")

            # РАБОТА С ПАМЯТЬЮ (СЕССИИ DJANGO)
            if 'chat_history' not in request.session:
                request.session['chat_history'] = []
            
            chat_history = request.session['chat_history']
            chat_history.append({"role": "user", "content": user_message})    

            # Если у компании в базе прописан свой промпт — берем его! 
            # Если нет — используем стандартный промпт автосалона Broom.
            system_prompt = ""
            if v_company and v_company.ai_prompt:
                system_prompt = v_company.ai_prompt
            else:
                system_prompt = (
                    "Ты — опытный менеджер по продажам автосалона 'Broom'. Твоя цель — помочь клиенту "
                    "с выбором автомобиля и ОБЯЗАТЕЛЬНО мотивировать его оставить свой номер телефона "
                    "для связи с менеджером или записи на тест-драйв. "
                    "Общайся вежливо, используй смайлики. Если клиент задает вопрос о наличии, "
                    "назови пару популярных моделей (Geely Coolray, Haval Jolion, Lada Vesta) "
                    "и сразу спроси: 'На какой номер телефона я могу записать вас на тест-драйв?' "
                    "ВАЖНО: Пиши ТОЛЬКО финальный ответ клиенту. Никаких рассуждений, заметок и внутренних мыслей вслух быть не должно!"
                )
            
            limited_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            messages_to_ai = [{"role": "system", "content": system_prompt}] + limited_history

            ai_response = ask_ai(messages_to_ai)

            chat_history.append({"role": "assistant", "content": ai_response})
            request.session['chat_history'] = chat_history

            return JsonResponse({"reply": ai_response})
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    return JsonResponse({"error": "Только POST запросы!"}, status=405)

@csrf_exempt
def clear_chat_api(request):
    if request.method == "POST":
        try:
            # Если в сессии браузера есть история, мы её удаляем
            if 'chat_history' in request.session:
                del request.session['chat_history']
                request.session.modified = True # Принудительно сохраняем сессию
                
            return JsonResponse({"success": True, "message": "История очищена"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
            
    return JsonResponse({"error": "Только POST запросы!"}, status=405)
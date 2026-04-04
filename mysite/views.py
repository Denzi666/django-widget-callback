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
            company_api_key = data.get("api_key", "")

            if not user_message:
                return JsonResponse({"error": "Сообщение пустое"}, status=400)
            
            v_company = None
            if company_api_key:
                v_company = Company.objects.filter(api_key=company_api_key).first()
            
            # 1. Сначала просто ищем телефон, но пока НИЧЕГО не отправляем в ТГ
            phone_pattern = r'(?:\+7|7|8)?[\s\-]?\(?[489]\d{2}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\b\d{10}\b'
            phones = re.findall(phone_pattern, user_message)
            
            detected_phone = phones[0] if phones else None

            # 2. РАБОТА С ПАМЯТЬЮ
            if 'chat_history' not in request.session:
                request.session['chat_history'] = []
            
            chat_history = request.session['chat_history']
            chat_history.append({"role": "user", "content": user_message})    

            # 3. ПОЛУЧАЕМ СИСТЕМНЫЙ ПРОМПТ
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

            # Генерируем обычный ответ для клиента в чате
            ai_response = ask_ai(messages_to_ai)

            # 4. 🔥 НОВАЯ МАГИЯ: ЕСЛИ НАЙДЕН ТЕЛЕФОН — ПРОСИМ ИИ СДЕЛАТЬ ВЫЖИМКУ!
            if detected_phone:
                # Формируем специальный технический запрос для ИИ на основе ПОСЛЕДНИХ сообщений
                summary_prompt = [
                    {"role": "system", "content": "Ты — технический ассистент. Твоя задача — прочитать диалог и ОДНОЙ КОРОТКОЙ ФРАЗОЙ (до 5-7 слов) написать, чего хотел клиент. Например: 'Запись на тест-драйв', 'Интересуется Haval Jolion', 'Просил перезвонить'. Пиши ТОЛЬКО эту фразу, без лишних слов, кавычек и точек."},
                ] + limited_history # Передаем историю, чтобы ИИ понял контекст
                
                # Запрашиваем у ИИ суть разговора
                client_intent_summary = ask_ai(summary_prompt)
                
                # Если ИИ выдал ошибку или пустую строку, подстрахуемся стандартной фразой
                if not client_intent_summary or "Ошибка ИИ:" in client_intent_summary:
                    client_intent_summary = "Оставил заявку в чате"

                # А вот теперь создаем запись в базе с КРАСИВЫМ сообщением
                Callback.objects.create(
                    name="Лид из Чата 🤖", 
                    phone=detected_phone, 
                    message=client_intent_summary.strip(), # Кладём выжимку ИИ вместо сырого текста
                    company=v_company
                )
    
                # Отправляем КРАСИВОЕ уведомление в Telegram
                tg_text = f"🔥 Новый лид из чата!\nНомер телефона: {detected_phone}\nСообщение: {client_intent_summary.strip()}"
                if v_company:
                    tg_text += f"\nКомпания: {v_company.name}"
                
                send_telegram_message(tg_text)
                print(f"ПЕРЕХВАЧЕН ТЕЛЕФОН: {detected_phone} С ЦЕЛЬЮ: {client_intent_summary}")

            # 5. Добавляем ответ ИИ в историю для клиента
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
from dotenv import load_dotenv
load_dotenv()  # Эта строка должна быть в самом начале

import os
import sys
import json
import base64
import asyncio
from telegram.ext import Application

async def run_diagnostics():
    print("=== ДИАГНОСТИКА ЛОКАЛЬНОГО ОКРУЖЕНИЯ ===")
    
    # 1. Проверка Python версии
    print(f"Python версия: {sys.version}")
    
    # 2. Проверка переменных окружения
    token = os.getenv('TOKEN')
    google_creds = os.getenv('GOOGLE_CREDENTIALS_BASE64')
    
    print(f"TOKEN установлен: {'Да' if token else 'Нет'}")
    if token:
        print(f"TOKEN (первые 10 символов): {token[:10]}...")
    
    print(f"GOOGLE_CREDENTIALS_BASE64 установлен: {'Да' if google_creds else 'Нет'}")
    
    # 3. Проверка импортов
    try:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        print("✅ telegram.ext импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта telegram.ext: {e}")
        return
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        print("✅ gspread и google.oauth2 импортированы успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта Google библиотек: {e}")
    
    # 4. Проверка подключения к Telegram
    if token:
        try:
            app = Application.builder().token(token).build()
            bot_info = await app.bot.get_me()
            print(f"✅ Подключение к Telegram успешно: @{bot_info.username}")
            print(f"   ID бота: {bot_info.id}")
            print(f"   Имя бота: {bot_info.first_name}")
        except Exception as e:
            print(f"❌ Ошибка подключения к Telegram: {e}")
    
    # 5. Проверка Google Credentials
    if google_creds:
        try:
            credentials_json = base64.b64decode(google_creds).decode('utf-8')
            credentials_data = json.loads(credentials_json)
            print("✅ Google credentials декодированы успешно")
            print(f"   Проект: {credentials_data.get('project_id', 'Не указан')}")
            print(f"   Email: {credentials_data.get('client_email', 'Не указан')}")
            
            # Попробуйте подключиться к Google Sheets
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                
                SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
                creds = Credentials.from_service_account_info(credentials_data, scopes=SCOPES)
                client = gspread.authorize(creds)
                print("✅ Подключение к Google Sheets API успешно")
            except Exception as e:
                print(f"❌ Ошибка подключения к Google Sheets: {e}")
                
        except Exception as e:
            print(f"❌ Ошибка обработки Google credentials: {e}")
    
    print("=== КОНЕЦ ДИАГНОСТИКИ ===")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())

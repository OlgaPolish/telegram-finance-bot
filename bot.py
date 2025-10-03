#!/usr/bin/env python
# coding: utf-8

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import os
import logging
import json
import base64
import tempfile

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Функция для получения credentials из переменной окружения
def get_google_credentials():
    # Попробуем получить credentials из Base64
    credentials_base64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
    if credentials_base64:
        try:
            # Декодируем Base64
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
            credentials_dict = json.loads(credentials_json)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(credentials_dict, temp_file)
                temp_file_path = temp_file.name
            
            return ServiceAccountCredentials.from_json_keyfile_name(temp_file_path, scope)
        except Exception as e:
            logger.error(f"Ошибка при обработке GOOGLE_CREDENTIALS_BASE64: {e}")
    
    # Если Base64 не работает, попробуем обычный файл
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'finance-bot-keys.json')
    if os.path.exists(credentials_file):
        return ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    
    raise Exception("Не найдены учетные данные Google. Установите GOOGLE_CREDENTIALS_BASE64 или поместите файл finance-bot-keys.json")

# Получаем credentials
creds = get_google_credentials()
client = gspread.authorize(creds)

# Название таблицы из переменной окружения или по умолчанию
sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'MY_Dvag')
sheet = client.open(sheet_name).sheet1

# --- TELEGRAM BOT ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise Exception("Не установлен TELEGRAM_BOT_TOKEN")

# Этапы диалога
TEMA, NAME, PHONE, DATE = range(4)

def get_current_datetime():
    """Получить текущую дату и время в среднеевропейском часовом поясе"""
    cet_tz = pytz.timezone('CET')  # Среднеевропейское время
    now = datetime.now(cet_tz)
    return now.strftime('%d.%m.%Y %H:%M:%S')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.effective_user.id} начал диалог")
    await update.message.reply_text(
        "Здравствуйте! Я финансовый консультант Ольга 👩‍💼\n \n" 
        "Вы можете записаться на консультацию по темам:  \n \n"   
        "1.💰 Личные финансы \n"
        "2.🏖️ Пенсионное планирование\n"
        "3.🛡️ Комплексные варианты страхования\n"
        "4.📈 Инвестиции  \n"
        "5.🏠 Ипотека\n"
        "6.💼 Бизнес-финансы\n"
        "7.📞 Другой вопрос\n \n"
        "Пожалуйста, напишите номер темы:"
    )
    return TEMA
    
async def get_tema(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tema"] = update.message.text
    await update.message.reply_text("Пожалуйста, напишите ваше имя:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Спасибо! Теперь укажите ваш номер телефона:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("Отлично 👍 Укажите желаемую дату консультации (например: 10.10.2025):")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text
    
    # Получаем текущую дату и время в среднеевропейском часовом поясе
    created_at = get_current_datetime()
    
    try:
        # Сохраняем в Google Sheets с добавлением времени создания записи
        sheet.append_row([
            context.user_data["tema"], 
            context.user_data["name"], 
            context.user_data["phone"], 
            context.user_data["date"],
            created_at  # Добавляем поле с датой и временем создания записи (среднеевропейское время)
        ])
        
        logger.info(f"Запись добавлена для пользователя {context.user_data['name']} в {created_at} (среднеевропейское время)")
        
        await update.message.reply_text(
            f"Спасибо, {context.user_data['name']}! 📅\n"
            "Вы записаны на консультацию. Мы свяжемся с вами для подтверждения!"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении в Google Sheets: {e}")
        await update.message.reply_text(
            "Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже или свяжитесь с администратором."
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.effective_user.id} отменил диалог")
    await update.message.reply_text("Запись отменена.")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}")

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tema)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    
    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
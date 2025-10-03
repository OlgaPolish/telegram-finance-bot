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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Получаем путь к файлу ключей из переменной окружения или используем по умолчанию
credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'finance-bot-keys.json')
creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
client = gspread.authorize(creds)

# Название таблицы из переменной окружения или по умолчанию
sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'MY_Dvag')
sheet = client.open(sheet_name).sheet1

# --- TELEGRAM BOT ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '456')

# Этапы диалога
TEMA, NAME, PHONE, DATE = range(4)

def get_current_datetime():
    """Получить текущую дату и время в московском часовом поясе"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
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
    
    # Получаем текущую дату и время
    created_at = get_current_datetime()
    
    try:
        # Сохраняем в Google Sheets с добавлением времени создания записи
        sheet.append_row([
            context.user_data["tema"], 
            context.user_data["name"], 
            context.user_data["phone"], 
            context.user_data["date"],
            created_at  # Добавляем поле с датой и временем создания записи
        ])
        
        logger.info(f"Запись добавлена для пользователя {context.user_data['name']} в {created_at}")
        
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
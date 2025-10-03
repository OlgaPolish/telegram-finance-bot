#!/usr/bin/env python
# coding: utf-8

from dotenv import load_dotenv
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import os
import logging
import json
import base64

# Настройка логирования
logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- GOOGLE SHEETS SETUP ---
SCOPES = [
  'https://www.googleapis.com/auth/spreadsheets',
  'https://www.googleapis.com/auth/drive'
]

def get_google_sheet():
  """Получение объекта Google Sheet - точно такая же логика как в тесте"""
  try:
      # Получаем credentials - ТОЧНО как в тесте
      credentials_base64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
      if credentials_base64:
          credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
          credentials_dict = json.loads(credentials_json)
          creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
      else:
          creds = Credentials.from_service_account_file('finance-bot-keys.json', scopes=SCOPES)
      
      # Подключаемся к Google Sheets - ТОЧНО как в тесте
      client = gspread.authorize(creds)
      sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'MY_Dvag')
      sheet = client.open(sheet_name).sheet1
      
      logger.info(f"✅ Подключение к Google Sheets '{sheet_name}' успешно")
      return sheet
      
  except Exception as e:
      logger.error(f"❌ Ошибка подключения к Google Sheets: {e}")
      return None

# --- TELEGRAM BOT ---
TOKEN = os.getenv('TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
  raise Exception("Не установлен TOKEN или TELEGRAM_BOT_TOKEN")

# Этапы диалога
TEMA, NAME, PHONE, DATE = range(4)

def get_current_datetime():
  """Получить текущую дату и время в среднеевропейском часовом поясе"""
  cet_tz = pytz.timezone('CET')
  now = datetime.now(cet_tz)
  return now.strftime('%d.%m.%Y %H:%M:%S')

def get_instagram_keyboard():
  """Создает клавиатуру с кнопкой Instagram"""
  keyboard = [
      [InlineKeyboardButton("📸 Подробнее в Instagram", url="https://www.instagram.com/olga_finance_/")]
  ]
  return InlineKeyboardMarkup(keyboard)

def get_main_keyboard():
  """Создает главную клавиатуру с опциями"""
  keyboard = [
      [InlineKeyboardButton("📝 Записаться на консультацию", callback_data="book_consultation")],
      [InlineKeyboardButton("📸 Узнать больше в Instagram", url="https://www.instagram.com/olga_finance_/")]
  ]
  return InlineKeyboardMarkup(keyboard)

def get_restart_keyboard():
  """Создает клавиатуру с кнопкой рестарта"""
  keyboard = [
      [InlineKeyboardButton("🔄 Начать заново", callback_data="restart")],
      [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/olga_finance_/")]
  ]
  return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Команда /start - всегда доступна"""
  logger.info(f"Пользователь {update.effective_user.id} начал диалог")
  
  # Очищаем данные пользователя при рестарте
  context.user_data.clear()
  
  await update.message.reply_text(
      "Здравствуйте! Я финансовый консультант Ольга 👩‍💼\n\n"
      "🎯 Помогаю людям:\n"
      "• Управлять личными финансами\n"
      "• Планировать пенсию\n"
      "• Выбирать страхование\n"
      "• Инвестировать грамотно\n"
      "• Оформлять ипотеку\n"
      "• Решать бизнес-задачи\n\n"
      "Выберите действие:",
      reply_markup=get_main_keyboard()
  )
  return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Обработчик нажатий на кнопки"""
  query = update.callback_query
  await query.answer()
  
  if query.data == "book_consultation":
      # Очищаем данные пользователя при новой записи
      context.user_data.clear()
      
      await query.edit_message_text(
          "Отлично! Давайте запишем вас на консультацию 📅\n\n"
          "Вы можете записаться на консультацию по темам:\n\n"   
          "1.💰 Личные финансы\n"
          "2.🏖️ Пенсионное планирование\n"
          "3.🛡️ Комплексные варианты страхования\n"
          "4.📈 Инвестиции\n"
          "5.🏠 Ипотека\n"
          "6.💼 Бизнес-финансы\n"
          "7.📞 Другой вопрос\n\n"
          "Пожалуйста, напишите номер темы:"      )
      return TEMA
  
  elif query.data == "restart":
      # Рестарт бота
      context.user_data.clear()
      
      await query.edit_message_text(
          "🔄 Начинаем заново!\n\n"
          "Здравствуйте! Я финансовый консультант Ольга 👩‍💼\n\n"
          "🎯 Помогаю людям:\n"
          "• Управлять личными финансами\n"
          "• Планировать пенсию\n"
          "• Выбирать страхование\n"
          "• Инвестировать грамотно\n"
          "• Оформлять ипотеку\n"
          "• Решать бизнес-задачи\n\n"
          "Выберите действие:",
          reply_markup=get_main_keyboard()
      )
      return ConversationHandler.END
  
  return ConversationHandler.END

async def get_tema(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data["tema"] = update.message.text
  await update.message.reply_text(
      "Пожалуйста, напишите ваше имя:"  )
  return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data["name"] = update.message.text
  await update.message.reply_text(
      "Спасибо! Теперь укажите ваш номер телефона:"  )
  return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data["phone"] = update.message.text
  await update.message.reply_text(
      "Отлично 👍 Укажите желаемую дату консультации (например: 10.10.2025):"  )
  return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data["date"] = update.message.text
  
  # Получаем текущую дату и время
  created_at = get_current_datetime()
  
  try:
      logger.info(f"Начинаем сохранение данных для пользователя {context.user_data['name']}")
      
      # Получаем sheet - используем ту же функцию что и в тесте
      sheet = get_google_sheet()
      
      if not sheet:
          logger.error("Не удалось получить объект Google Sheet")
          await update.message.reply_text(
              "❌ Произошла ошибка при подключении к базе данных.\n\n"
              "Пожалуйста, попробуйте позже или свяжитесь со мной напрямую через Instagram:",
              reply_markup=get_restart_keyboard()
          )
          return ConversationHandler.END
      
      # Подготавливаем данные для записи
      row_data = [
          context.user_data["tema"], 
          context.user_data["name"], 
          context.user_data["phone"], 
          context.user_data["date"],
          created_at
      ]
      
      logger.info(f"Данные для сохранения: {row_data}")
      
      # Сохраняем в Google Sheets - ТОЧНО как в тесте
      sheet.append_row(row_data)
      
      logger.info(f"✅ Запись успешно добавлена для пользователя {context.user_data['name']} в {created_at}")
      
      # Создаем клавиатуру для успешной записи
      success_keyboard = [
          [InlineKeyboardButton("📝 Записаться еще раз", callback_data="book_consultation")],
          [InlineKeyboardButton("🔄 Главное меню", callback_data="restart")],
          [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/olga_finance_/")]
      ]
      success_markup = InlineKeyboardMarkup(success_keyboard)
      
      await update.message.reply_text(
          f"Спасибо, {context.user_data['name']}! 🎉\n\n"
          "✅ Вы успешно записаны на консультацию!\n"
          "📞 Мы свяжемся с вами для подтверждения времени и деталей.\n\n"
          "💡 Что дальше?",
          reply_markup=success_markup
      )
      
  except Exception as e:
      logger.error(f"❌ Ошибка при сохранении данных: {e}")
      logger.error(f"❌ Тип ошибки: {type(e).__name__}")
      
      await update.message.reply_text(
          "❌ Произошла ошибка при сохранении данных.\n\n"
          "Пожалуйста, попробуйте позже или свяжитесь со мной напрямую через Instagram.\n"
          "Я обязательно помогу вам с записью! 😊",
          reply_markup=get_restart_keyboard()
      )
  
  return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  logger.info(f"Пользователь {update.effective_user.id} отменил диалог")
  await update.message.reply_text(
      "Запись отменена. 😊\n\n"
      "Если передумаете или у вас возникнут вопросы, всегда можете связаться со мной:",
      reply_markup=get_restart_keyboard()
  )
  return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Команда помощи"""
  await update.message.reply_text(
      "🆘 Помощь по боту:\n\n"
      "• /start - начать или перезапустить бота\n"
      "• /help - показать эту справку\n"
      "• /cancel - отменить текущую запись\n\n"
      "🔄 Чтобы начать заново в любой момент:\n"
      "• Напишите /start\n"
      "• Или нажмите кнопку 'Начать заново'\n\n"
      "📞 Если у вас технические проблемы с ботом, свяжитесь со мной напрямую:",
      reply_markup=get_restart_keyboard()
  )

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Обработчик неизвестных сообщений вне диалога"""
  await update.message.reply_text(
      "Привет! 👋\n\n"
      "Чтобы начать работу с ботом, нажмите /start или выберите действие:",
      reply_markup=get_main_keyboard()
  )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  """Обработчик ошибок"""
  logger.error(f"Произошла ошибка в боте: {context.error}")
  
  # Если есть update и message, отправляем сообщение об ошибке
  if update and update.effective_message:
      try:
          await update.effective_message.reply_text(
              "❌ Произошла техническая ошибка.\n\n"
              "Пожалуйста, попробуйте еще раз или свяжитесь со мной напрямую:",
              reply_markup=get_restart_keyboard()
          )
      except Exception as e:
          logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

def main():
  # Проверяем подключение к Google Sheets при запуске
  print("🔍 Проверяем подключение к Google Sheets...")
  test_sheet = get_google_sheet()
  if test_sheet:
      print("✅ Подключение к Google Sheets работает!")
  else:
      print("❌ Ошибка подключения к Google Sheets!")
      return
  
  # Создаем приложение бота
  app = Application.builder().token(TOKEN).build()

  # Настраиваем обработчик диалога
  conv_handler = ConversationHandler(
      entry_points=[
          CallbackQueryHandler(button_handler, pattern="^book_consultation$")
      ],
      states={
          TEMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tema)],
          NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
          PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
          DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
      },
      fallbacks=[CommandHandler("cancel", cancel)],
  )

  # Добавляем обработчики
  app.add_handler(CommandHandler("start", start))  # /start всегда доступен
  app.add_handler(CommandHandler("help", help_command))
  app.add_handler(conv_handler)
  app.add_handler(CallbackQueryHandler(button_handler))  # Обработчик кнопок
  
  # Обработчик неизвестных сообщений (когда пользователь пишет что-то вне диалога)
  app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))
  
  app.add_error_handler(error_handler)
  
  logger.info("🚀 Бот запущен!")
  print("🚀 Бот запущен! Нажмите Ctrl+C для остановки")
  app.run_polling()

if __name__ == "__main__":
  main()
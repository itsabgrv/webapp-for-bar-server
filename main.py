from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, WebAppInfo, MenuButtonWebApp, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import logging
import asyncio
import json

# Настройки
TOKEN = "7679529575:AAGWh3tDwjdaF8vjVs9GP1e5a-xa-oKvWVQ"
FRONTEND_URL = "https://webapp-for-bar-front-git-main-adams-projects-62b06f32.vercel.app"
SUPABASE_URL = "https://okepiftwlqymibftguid.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # сократи ключ

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS — разрешаем фронтенд домен и локальные тесты
origins = [
    FRONTEND_URL,
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # разрешаем все методы
    allow_headers=["*"],
)

# Инициализация Telegram Application (бота)
tg_app = ApplicationBuilder().token(TOKEN).build()

@app.get("/")
async def root():
    return {"message": "Server is running"}

@app.post("/notify")
async def notify(request: Request):
    try:
        data = await request.json()
        logger.info(f"📩 Получен запрос /notify: {data}")

        user_id = data.get("user_id")
        if not user_id:
            logger.error("❌ В запросе отсутствует user_id")
            return {"error": "user_id not found"}

        # Формируем текст сообщения
        services = data.get("services", [])
        services_text = "\n".join(f"— {s['title']} ({s['price']} ₸)" for s in services) if services else "—"

        msg = (
            f"✅ Вы записались!\n\n"
            f"📅 Дата: {data.get('date', '—')} в {data.get('time', '—')}\n"
            f"👤 Мастер: {data.get('specialist', '—')}\n"
            f"📍 Филиал: {data.get('branch', '—')}\n\n"
            f"💼 Услуги:\n{services_text}\n\n"
            f"🧑 Имя: {data.get('name', '—')}\n"
            f"📞 Телефон: {data.get('phone', '—')}\n"
            f"✉️ Email: {data.get('email', '—')}\n"
            f"💬 Комментарий: {data.get('comment', '—')}"
        )

        logger.info(f"Попытка отправить сообщение пользователю {user_id}...")
        await tg_app.bot.send_message(chat_id=user_id, text=msg)
        logger.info("Сообщение успешно отправлено")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Ошибка в /notify: {e}")
        return {"error": str(e)}

# /start команда для Telegram бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [KeyboardButton("💈 Записаться", web_app=WebAppInfo(url=FRONTEND_URL))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Нажмите кнопку ниже 👇", reply_markup=reply_markup)

# Обработка web_app_data (sendData из WebApp)
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        logger.info("📦 Получены данные из WebApp: %s", data)

        services = data.get("services", [])
        services_text = "\n".join(f"— {s['title']} ({s['price']} ₸)" for s in services) if services else "—"

        msg = (
            f"✅ Вы записались!\n\n"
            f"📅 Дата: {data.get('date', '—')} в {data.get('time', '—')}\n"
            f"👤 Мастер: {data.get('specialist', '—')}\n"
            f"📍 Филиал: {data.get('branch', '—')}\n\n"
            f"💼 Услуги:\n{services_text}\n\n"
            f"🧑 Имя: {data.get('name', '—')}\n"
            f"📞 Телефон: {data.get('phone', '—')}\n"
            f"✉️ Email: {data.get('email', '—')}\n"
            f"💬 Комментарий: {data.get('comment', '—')}"
        )

        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке web_app_data: {e}")
        await update.message.reply_text("Произошла ошибка при обработке записи 😞")

# Установка кнопки MenuButtonWebApp при старте бота
async def setup_menu(app):
    await app.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="💈 Записаться",
            web_app=WebAppInfo(url=FRONTEND_URL)
        )
    )
    logger.info("✅ Кнопка меню WebApp установлена")

# Запуск Telegram бота через asyncio
async def run_telegram():
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    tg_app.post_init = setup_menu

    logger.info("🚀 Запуск Telegram бота...")
    await tg_app.run_polling()

# Запуск бота и FastAPI вместе
@app.on_event("startup")
async def startup_event():
    logger.info("⚙️ Запускаем Telegram бота как фоновую задачу")
    asyncio.create_task(run_telegram())

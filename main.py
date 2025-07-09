from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, WebAppInfo, MenuButtonWebApp, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import logging
import asyncio
import json
import os

# === НАСТРОЙКИ ===
TOKEN = os.getenv("BOT_TOKEN")
FRONTEND_URL = "https://webapp-for-bar-front-git-main-adams-projects-62b06f32.vercel.app"

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === FASTAPI app ===
app = FastAPI()

origins = [
    FRONTEND_URL,
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Telegram Bot ===
tg_app: Application = Application.builder().token(TOKEN).build()

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
            return {"error": "user_id not found"}

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

        await tg_app.bot.send_message(chat_id=user_id, text=msg)
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Ошибка в /notify: {e}")
        return {"error": str(e)}

# === Команды и хендлеры ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("💈 Записаться", web_app=WebAppInfo(url=FRONTEND_URL))]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Нажмите кнопку ниже 👇", reply_markup=markup)
    logger.info("🚀 Бот и сервер FastAPI полностью запущены")


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        logger.info("📦 Получены данные из WebApp: %s", data)

        services = data.get("services", [])
        services_text = "\n".join(f"— {s['title']} ({s['price']} ₸)" for s in services) if services else "—"

        msg = (
            f"✅ Вы записались!\n\n"
            f"📅 Дата: {data.get('date')} в {data.get('time')}\n"
            f"👤 Мастер: {data.get('specialist')}\n"
            f"📍 Филиал: {data.get('branch')}\n\n"
            f"💼 Услуги:\n{services_text}\n\n"
            f"🧑 Имя: {data.get('name')}\n"
            f"📞 Телефон: {data.get('phone')}\n"
            f"✉️ Email: {data.get('email')}\n"
            f"💬 Комментарий: {data.get('comment')}"
        )

        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке web_app_data: {e}")
        await update.message.reply_text("Произошла ошибка при обработке записи 😞")

# === Запуск бота при старте FastAPI ===
@app.on_event("startup")
async def startup_event():
    logger.info("⚙️ Запускаем Telegram бота как фоновую задачу")

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    await tg_app.initialize()  # ✅ сначала инициализация
    await tg_app.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="💈 Записаться",
            web_app=WebAppInfo(url=FRONTEND_URL)
        )
    )
    await tg_app.start()
    logger.info("✅ Telegram бот успешно запущен")


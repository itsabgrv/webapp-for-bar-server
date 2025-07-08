import asyncio
import logging

from fastapi import FastAPI
from telegram import Update, BotCommand, WebAppInfo, MenuButtonWebApp
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("7651271495:AAFrdL7sxLEx0dcvCTsJr73uabpeZ38oYng")

# Инициализация FastAPI
app = FastAPI()

# Инициализация Telegram бота
tg_app = ApplicationBuilder().token(TOKEN).build()

# Хэндлер команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Нажми кнопку ниже 👇", reply_markup={
        "keyboard": [[{
            "text": "💈 Записаться",
            "web_app": WebAppInfo(url="https://webapp-for-bar-front-git-main-adams-projects-62b06f32.vercel.app/")
        }]],
        "resize_keyboard": True
    })

# Добавляем хэндлер
tg_app.add_handler(CommandHandler("start", start))

# ✅ Асинхронный запуск телеграм-бота
async def run_telegram():
    await tg_app.initialize()
    await tg_app.start()
    print("🚀 Бот запущен")
    await tg_app.updater.start_polling()
    await tg_app.updater.wait()

# Запуск бота при старте приложения
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_telegram())

@app.get("/")
async def root():
    return {"message": "🤖 Telegram bot is running!"}

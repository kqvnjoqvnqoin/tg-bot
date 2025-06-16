# bot.py

from background import keep_alive
keep_alive()

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7824657091:AAEIbNr19dyNUzdcdwbNS9_CdExrC4kJlTc"  # <-- Вставь сюда свой токен
CHANNEL_ID = -1002537468527   # <-- Твой channel_id
USER_ID_FILE = "user_id.txt"

(
    MOOD, SLEEP, CALORIES, ACTIVITY_YN, ACTIVITY_KCAL,
    BOOK_YN, BOOK_PAGES, VIDEO_YN, VIDEO_COUNT,
    SPECIAL_CONTENT_YN, SPECIAL_CONTENT_INPUT, SPECIAL_CONTENT_MORE,
    SONG_YN, SONG_INPUT
) = range(14)

def save_user_id(user_id):
    with open(USER_ID_FILE, "w") as f:
        f.write(str(user_id))

def load_user_id():
    if os.path.exists(USER_ID_FILE):
        with open(USER_ID_FILE, "r") as f:
            return int(f.read().strip())
    return None

def get_mood_keyboard():
    keyboard = [
        ["плохое [-2]", "не оч [-1]"],
        ["обычное [0]"],
        ["хорошее [+1]", "отличное [+2]"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_yes_no_keyboard():
    keyboard = [
        [KeyboardButton("Да"), KeyboardButton("Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    save_user_id(update.effective_user.id)
    await update.message.reply_text(
        "Здравствуйте, как ваше настроение?",
        reply_markup=get_mood_keyboard()
    )
    return MOOD

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    save_user_id(update.effective_user.id)
    await update.message.reply_text(
        "Тестовый запуск сводки!\n\nЗдравствуйте, как ваше настроение?",
        reply_markup=get_mood_keyboard()
    )
    return MOOD

async def mood_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mood_map = {
        "плохое [-2]": "плохое [-2]",
        "не оч [-1]": "не оч [-1]",
        "обычное [0]": "обычное [0]",
        "хорошее [+1]": "хорошее [+1]",
        "отличное [+2]": "отличное [+2]"
    }
    mood = mood_map.get(update.message.text)
    if mood:
        context.user_data['mood'] = mood
        await update.message.reply_text(
            f"Спасибо за ответ! Ваше настроение: {mood}\nСколько вы сегодня спали? (например: 7 30)",
            reply_markup=ReplyKeyboardRemove()
        )
        return SLEEP
    else:
        await update.message.reply_text("Пожалуйста, выбери вариант с клавиатуры.")
        return MOOD

async def sleep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        hours = int(parts[0])
        minutes = int(parts[1])
        context.user_data['sleep'] = f"{hours} ч. {minutes} мин."
        await update.message.reply_text(f"Сон: {hours} ч. {minutes} мин.\nСколько калорий вы сегодня употребили?")
        return CALORIES
    else:
        await update.message.reply_text("Пожалуйста, введите время в формате: часы минуты (например: 7 30)")
        return SLEEP

async def calories_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        context.user_data['calories'] = text
        await update.message.reply_text(
            f"{text} кк.\nВы занимались сегодня активностью?",
            reply_markup=get_yes_no_keyboard()
        )
        return ACTIVITY_YN
    else:
        await update.message.reply_text("Пожалуйста, введите только число калорий (например: 2134)")
        return CALORIES

async def activity_yn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip().lower()
    if answer == "да":
        context.user_data['activity'] = "Да"
        await update.message.reply_text(
            "Сколько активных калорий?",
            reply_markup=ReplyKeyboardRemove()
        )
        return ACTIVITY_KCAL
    elif answer == "нет":
        context.user_data['activity'] = "Нет"
        context.user_data['activity_kcal'] = "—"
        await update.message.reply_text(
            "Вы читали сегодня книгу?",
            reply_markup=get_yes_no_keyboard()
        )
        return BOOK_YN
    else:
        await update.message.reply_text(
            "Пожалуйста, выбери 'Да' или 'Нет' с клавиатуры.",
            reply_markup=get_yes_no_keyboard()
        )
        return ACTIVITY_YN

async def activity_kcal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        context.user_data['activity_kcal'] = text
        await update.message.reply_text(
            f"{text} активных кк.\nВы читали сегодня книгу?",
            reply_markup=get_yes_no_keyboard()
        )
        return BOOK_YN
    else:
        await update.message.reply_text("Пожалуйста, введите только число активных калорий (например: 1255)")
        return ACTIVITY_KCAL

async def book_yn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip().lower()
    if answer == "да":
        context.user_data['book'] = "Да"
        await update.message.reply_text(
            "Сколько страниц Вы прочитали?",
            reply_markup=ReplyKeyboardRemove()
        )
        return BOOK_PAGES
    elif answer == "нет":
        context.user_data['book'] = "Нет"
        context.user_data['book_pages'] = "—"
        await update.message.reply_text(
            "Вы смотрели сегодня видео?",
            reply_markup=get_yes_no_keyboard()
        )
        return VIDEO_YN
    else:
        await update.message.reply_text(
            "Пожалуйста, выбери 'Да' или 'Нет' с клавиатуры.",
            reply_markup=get_yes_no_keyboard()
        )
        return BOOK_YN

async def book_pages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        context.user_data['book_pages'] = text
        await update.message.reply_text(
            f"Прочитано {text} страниц.\nВы смотрели сегодня видео?",
            reply_markup=get_yes_no_keyboard()
        )
        return VIDEO_YN
    else:
        await update.message.reply_text("Пожалуйста, введите только число страниц (например: 40)")
        return BOOK_PAGES

async def video_yn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip().lower()
    if answer == "да":
        context.user_data['video'] = "Да"
        await update.message.reply_text(
            "Сколько видео вы сегодня просмотрели?",
            reply_markup=ReplyKeyboardRemove()
        )
        return VIDEO_COUNT
    elif answer == "нет":
        context.user_data['video'] = "Нет"
        context.user_data['video_count'] = "—"
        await update.message.reply_text(
            "Сегодня есть особый контент?",
            reply_markup=get_yes_no_keyboard()
        )
        return SPECIAL_CONTENT_YN
    else:
        await update.message.reply_text(
            "Пожалуйста, выбери 'Да' или 'Нет' с клавиатуры.",
            reply_markup=get_yes_no_keyboard()
        )
        return VIDEO_YN

async def video_count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        context.user_data['video_count'] = text
        await update.message.reply_text(
            f"Просмотрено {text} видео.\nСегодня есть особый контент?",
            reply_markup=get_yes_no_keyboard()
        )
        return SPECIAL_CONTENT_YN
    else:
        await update.message.reply_text("Пожалуйста, введите только число видео (например: 2)")
        return VIDEO_COUNT

async def special_content_yn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip().lower()
    if answer == "да":
        context.user_data['special_content'] = []
        await update.message.reply_text(
            "Поделитесь особым контентом",
            reply_markup=ReplyKeyboardRemove()
        )
        return SPECIAL_CONTENT_INPUT
    elif answer == "нет":
        await ask_song_of_the_day(update, context)
        return SONG_YN
    else:
        await update.message.reply_text(
            "Пожалуйста, выбери 'Да' или 'Нет' с клавиатуры.",
            reply_markup=get_yes_no_keyboard()
        )
        return SPECIAL_CONTENT_YN

async def special_content_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = update.message.text.strip()
    if 'special_content' not in context.user_data:
        context.user_data['special_content'] = []
    context.user_data['special_content'].append(content)
    await update.message.reply_text(
        "добавлен особый контент, поделитесь еще?",
        reply_markup=get_yes_no_keyboard()
    )
    return SPECIAL_CONTENT_MORE

async def special_content_more_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip().lower()
    if answer == "да":
        await update.message.reply_text(
            "Поделитесь особым контентом",
            reply_markup=ReplyKeyboardRemove()
        )
        return SPECIAL_CONTENT_INPUT
    elif answer == "нет":
        await ask_song_of_the_day(update, context)
        return SONG_YN
    else:
        await update.message.reply_text(
            "Пожалуйста, выбери 'Да' или 'Нет' с клавиатуры.",
            reply_markup=get_yes_no_keyboard()
        )
        return SPECIAL_CONTENT_MORE

async def ask_song_of_the_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Есть композиция дня?",
        reply_markup=get_yes_no_keyboard()
    )

async def song_yn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip().lower()
    if answer == "да":
        await update.message.reply_text(
            "Напиши композицию дня (Название композиции - Исполнитель):",
            reply_markup=ReplyKeyboardRemove()
        )
        return SONG_INPUT
    elif answer == "нет":
        context.user_data['song_of_the_day'] = None
        await send_summary_and_finish(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Пожалуйста, выбери 'Да' или 'Нет' с клавиатуры.",
            reply_markup=get_yes_no_keyboard()
        )
        return SONG_YN

async def song_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    song = update.message.text.strip()
    context.user_data['song_of_the_day'] = song
    await send_summary_and_finish(update, context)
    return ConversationHandler.END

async def send_summary_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    lines = ["📝 дейли:"]

    # Настроение
    mood = data.get('mood')
    if mood:
        lines.append(f"настроение: {mood}")

    # Сон
    sleep = data.get('sleep')
    if sleep and sleep != "—":
        lines.append(f"сон: {sleep}")

    # Калории
    calories = data.get('calories')
    if calories and calories != "—":
        lines.append(f"кк.: {calories}")

    # Активные ккал
    activity = data.get('activity')
    activity_kcal = data.get('activity_kcal')
    if activity == "Да" and activity_kcal and activity_kcal != "—":
        lines.append(f"активные кк.: {activity_kcal}")

    # Страниц книги
    book = data.get('book')
    book_pages = data.get('book_pages')
    if book == "Да" and book_pages and book_pages != "—":
        lines.append(f"страниц: {book_pages}")

    # Количество видео
    video = data.get('video')
    video_count = data.get('video_count')
    if video == "Да" and video_count and video_count != "—":
        lines.append(f"количество видео: {video_count}")

    summary = "\n".join(lines)

    # Отправляем итоговую сводку в канал
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=summary)
    except Exception as e:
        await update.message.reply_text(f"Ошибка отправки в канал: {e}", reply_markup=ReplyKeyboardRemove())
        return

    # Особый контент отдельным сообщением только в канал
    special_content = data.get('special_content', [])
    if special_content:
        content_text = "🌍 контент:\n" + "\n".join(f"{i+1}. {item}" for i, item in enumerate(special_content))
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=content_text,
                disable_web_page_preview=True
            )
        except Exception as e:
            await update.message.reply_text(f"Ошибка отправки особого контента в канал: {e}", reply_markup=ReplyKeyboardRemove())

    # Композиция дня отдельным сообщением только в канал
    song = data.get('song_of_the_day')
    if song:
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🔊 композиция дня: {song}"
            )
        except Exception as e:
            await update.message.reply_text(f"Ошибка отправки композиции дня в канал: {e}", reply_markup=ReplyKeyboardRemove())

    # В личку только финальное сообщение
    await update.message.reply_text(
        "Спасибо! Опрос завершён.",
        reply_markup=ReplyKeyboardRemove()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Опрос отменён.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Напоминание в 19:00 по МСК
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    user_id = load_user_id()
    if user_id:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="Напоминание: не забудь создать сводку за день с помощью /start или /test."
            )
        except Exception as e:
            logging.error(f"Ошибка отправки напоминания: {e}")

async def on_startup(app):
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_job(
        send_reminder,
        CronTrigger(hour=19, minute=0),
        args=[app]
    )
    scheduler.start()
    logging.info("Планировщик запущен.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("test", test)
        ],
        states={
            MOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, mood_handler)],
            SLEEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, sleep_handler)],
            CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, calories_handler)],
            ACTIVITY_YN: [MessageHandler(filters.TEXT & ~filters.COMMAND, activity_yn_handler)],
            ACTIVITY_KCAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, activity_kcal_handler)],
            BOOK_YN: [MessageHandler(filters.TEXT & ~filters.COMMAND, book_yn_handler)],
            BOOK_PAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, book_pages_handler)],
            VIDEO_YN: [MessageHandler(filters.TEXT & ~filters.COMMAND, video_yn_handler)],
            VIDEO_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, video_count_handler)],
            SPECIAL_CONTENT_YN: [MessageHandler(filters.TEXT & ~filters.COMMAND, special_content_yn_handler)],
            SPECIAL_CONTENT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, special_content_input_handler)],
            SPECIAL_CONTENT_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, special_content_more_handler)],
            SONG_YN: [MessageHandler(filters.TEXT & ~filters.COMMAND, song_yn_handler)],
            SONG_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, song_input_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.post_init = on_startup

    print("Бот запущен. Ожидает команду /start или /test в Telegram.")
    app.run_polling()

if __name__ == "__main__":
    main()

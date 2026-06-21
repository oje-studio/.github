"""Telegram-бот: ссылка -> скачивание в макс. качестве -> Google Drive -> ссылка в чат."""
import asyncio
import logging
import re
import shutil
import uuid
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import settings
from downloader import DownloadError, download_media
from uploader import UploadError, upload_file

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("studio-grabber.bot")

URL_RE = re.compile(r"https?://\S+")

HELP = (
    "👋 Пришли мне ссылку на видео/фото (YouTube, Instagram, TikTok, X и др.) — "
    "я скачаю в максимальном качестве, залью в Google Drive студии и пришлю ссылку.\n\n"
    "Можно несколько ссылок в одном сообщении."
)


def _authorized(update: Update) -> bool:
    if not settings.allowed_user_ids:
        return True  # открытый режим
    user = update.effective_user
    return bool(user and user.id in settings.allowed_user_ids)


async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP)


async def _process_url(update: Update, url: str) -> None:
    chat = update.effective_chat
    work_dir = settings.download_dir / uuid.uuid4().hex
    try:
        await chat.send_action(ChatAction.TYPING)
        status = await update.message.reply_text(f"⏳ Качаю: {url}")

        files = await asyncio.to_thread(download_media, url, work_dir)

        await status.edit_text(f"☁️ Скачано {len(files)} файл(ов), заливаю в Drive…")
        for f in files:
            link = await asyncio.to_thread(upload_file, f)
            size_mb = f.stat().st_size / (1024 * 1024)
            await update.message.reply_text(
                f"✅ <b>{f.name}</b> ({size_mb:.1f} МБ)\n{link}",
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
        await status.delete()
    except DownloadError as exc:
        await update.message.reply_text(f"❌ Не скачалось: {exc}")
    except UploadError as exc:
        await update.message.reply_text(f"❌ Ошибка заливки в Drive: {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Необработанная ошибка для %s", url)
        await update.message.reply_text(f"❌ Непредвиденная ошибка: {exc}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def on_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        await update.message.reply_text("⛔ Нет доступа. Обратись к администратору студии.")
        return

    urls = URL_RE.findall(update.message.text or "")
    if not urls:
        await update.message.reply_text("Пришли ссылку на медиа 🙂")
        return

    for url in urls:
        await _process_url(update, url)


def main() -> None:
    settings.validate()
    settings.download_dir.mkdir(parents=True, exist_ok=True)

    app = Application.builder().token(settings.bot_token).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    logger.info("Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

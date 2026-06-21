# Studio Grabber Bot

Telegram-бот для студии: присылаешь ссылку на видео/фото → бот скачивает в
**максимальном качестве** (`yt-dlp` + `gallery-dl`), заливает в **Google Drive**
студии и присылает ссылку на скачивание.

Стратегия: **всё через облако + ссылка** — нет ограничения Telegram в 50 МБ,
тяжёлое 4K-видео с ивентов отдаётся без проблем.

## Что поддерживается

- **Видео/аудио** (`yt-dlp`): YouTube, TikTok, Vimeo, X/Twitter, видео из Instagram и [1000+ сайтов](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).
- **Фото/галереи** (`gallery-dl`): посты и карусели Instagram, X/Twitter, Pinterest и др.
- Файлы складываются в Drive в подпапки по дате (`ГГГГ-ММ-ДД`) — удобно под раскладку ивентов.

## Архитектура

```
Telegram-ссылка
   │
   ▼
bot.py ──> downloader.py ──┬─ yt-dlp     (видео, макс. качество, склейка ffmpeg)
   │                       └─ gallery-dl (фото/галереи, fallback)
   │
   ▼
uploader.py ──> Google Drive (папка студии) ──> ссылка в чат
```

## Установка (VPS)

### 1. Бот в Telegram
1. Напиши [@BotFather](https://t.me/BotFather) → `/newbot` → получи **токен**.
2. (Опц.) Узнай свой Telegram user id у [@userinfobot](https://t.me/userinfobot) — для белого списка.

### 2. Google Drive (сервисный аккаунт)
1. В [Google Cloud Console](https://console.cloud.google.com/) создай проект.
2. Включи **Google Drive API**.
3. Создай **Service Account** → ключ в формате **JSON** → сохрани как `service_account.json`.
4. Скопируй email сервисного аккаунта (вида `...@...iam.gserviceaccount.com`).
5. В Google Drive **расшарь папку студии** на этот email с правом **Редактор**.
6. ID папки — из её URL: `drive.google.com/drive/folders/`**`<ЭТО_ID>`**.

> Сервисные аккаунты не имеют своей квоты Drive — заливай в папку на обычном/Shared Drive, расшаренную на аккаунт.

### 3. Конфиг
```bash
cp .env.example .env
# заполни TELEGRAM_BOT_TOKEN, GDRIVE_FOLDER_ID, ALLOWED_USER_IDS
# положи service_account.json рядом
```

### 4. Запуск

**Docker (рекомендуется):**
```bash
docker compose up -d --build
docker compose logs -f
```

**Локально:**
```bash
sudo apt install ffmpeg           # нужен yt-dlp
pip install -r requirements.txt
python bot.py
```

## Использование
Пишешь боту ссылку (или несколько в одном сообщении) — в ответ приходит
имя файла, размер и ссылка на Google Drive.

## Настройки (`.env`)
| Переменная | Назначение |
|---|---|
| `TELEGRAM_BOT_TOKEN` | токен от @BotFather |
| `GDRIVE_FOLDER_ID` | папка студии в Drive |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | путь к JSON-ключу |
| `ALLOWED_USER_IDS` | белый список id (пусто = всем) |
| `MAKE_PUBLIC` | публичная ссылка «всем, у кого есть ссылка» |
| `DATE_SUBFOLDERS` | раскладка по подпапкам с датой |

## Дальнейшие доработки
- Раскладка по **ивенту/команде**, а не только по дате (распознавать из текста сообщения).
- Прогресс скачивания крупных файлов.
- Очередь и параллельная обработка нескольких ссылок.
- Дедупликация по хэшу, чтобы не заливать одно и то же дважды.

## Лицензии используемых движков
- `yt-dlp` — Unlicense (public domain), можно встраивать свободно.
- `gallery-dl` — GPL-2.0: вызывается как внешний процесс, копилефт на код бота не распространяется.

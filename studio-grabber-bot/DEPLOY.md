# Деплой на VPS (Ubuntu/Debian)

Готовый сценарий для чистого сервера. Два варианта — выбери один.
**Docker — рекомендуется** (проще, изолированно, ffmpeg внутри).

---

## Вариант A. Docker (рекомендуется)

### 1. Установить Docker (один раз)
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker   # чтобы docker без sudo
```

### 2. Забрать код
```bash
git clone <URL-репозитория> studio-grabber
cd studio-grabber/studio-grabber-bot
```

### 3. Положить секреты
```bash
cp .env.example .env
nano .env          # впиши TELEGRAM_BOT_TOKEN, GDRIVE_FOLDER_ID, ALLOWED_USER_IDS
# скопируй сюда service_account.json (например, через scp с локальной машины):
#   scp service_account.json user@SERVER_IP:~/studio-grabber/studio-grabber-bot/
```

### 4. Запустить
```bash
docker compose up -d --build
docker compose logs -f          # ждём строку "Бот запущен"
```

### Управление
```bash
docker compose restart          # перезапуск
docker compose down             # остановить
docker compose pull && docker compose up -d --build   # после git pull
```
`restart: unless-stopped` в compose уже обеспечивает автозапуск после ребута сервера.

### Обновление кода
```bash
git pull
docker compose up -d --build
```

---

## Вариант B. Без Docker (systemd)

### 1. Зависимости
```bash
sudo apt update
sudo apt install -y python3-venv python3-pip ffmpeg git
```

### 2. Код и окружение
```bash
git clone <URL-репозитория> ~/studio-grabber
cd ~/studio-grabber/studio-grabber-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env       # заполни
# положи рядом service_account.json
```

### 3. systemd-сервис
```bash
sudo cp deploy/studio-grabber-bot.service /etc/systemd/system/
sudo nano /etc/systemd/system/studio-grabber-bot.service   # поправь User и пути под себя
sudo systemctl daemon-reload
sudo systemctl enable --now studio-grabber-bot
```

### Управление
```bash
systemctl status studio-grabber-bot
journalctl -u studio-grabber-bot -f      # логи
sudo systemctl restart studio-grabber-bot
```

### Обновление
```bash
cd ~/studio-grabber/studio-grabber-bot
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart studio-grabber-bot
```

---

## Проверка
Напиши боту `/start`, затем кинь любую ссылку. В ответ — имя файла, размер и
ссылка на Google Drive. Если ошибка — смотри логи (`docker compose logs -f`
или `journalctl -u studio-grabber-bot -f`).

## Частые проблемы
| Симптом | Причина / решение |
|---|---|
| `Не настроено окружение...` | не заполнен `.env` или нет `service_account.json` |
| Бот молчит | проверь `TELEGRAM_BOT_TOKEN`; не запущена ли вторая копия с тем же токеном |
| `⛔ Нет доступа` | твой Telegram ID не в `ALLOWED_USER_IDS` (или оставь пусто для всех) |
| Ошибка заливки в Drive | папка не расшарена на email сервисного аккаунта с правом «Редактор» |
| Видео не качается / 403 | для части сайтов нужны cookies — см. раздел cookies в README yt-dlp |

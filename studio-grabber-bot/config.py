"""Конфигурация бота. Все значения берутся из переменных окружения (.env)."""
import os
from dataclasses import dataclass, field
from pathlib import Path


def _parse_ids(raw: str) -> set[int]:
    """'123, 456 789' -> {123, 456, 789}"""
    return {int(x) for x in raw.replace(",", " ").split() if x.strip().isdigit()}


@dataclass(frozen=True)
class Settings:
    # Токен от @BotFather
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # ID папки Google Drive, куда заливаются файлы (из URL папки)
    gdrive_folder_id: str = os.getenv("GDRIVE_FOLDER_ID", "")
    # Путь к JSON сервисного аккаунта Google
    gdrive_service_account_file: str = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json"
    )
    # Делать ли ссылку доступной "всем, у кого есть ссылка"
    make_public: bool = os.getenv("MAKE_PUBLIC", "true").lower() == "true"
    # Складывать ли файлы в подпапку по дате (ГГГГ-ММ-ДД).
    # По умолчанию выключено: всё в одну папку-копилку референсов.
    date_subfolders: bool = os.getenv("DATE_SUBFOLDERS", "false").lower() == "true"

    # Временная папка для скачивания (чистится после отправки)
    download_dir: Path = Path(os.getenv("DOWNLOAD_DIR", "/tmp/studio-grabber"))

    # Кто может пользоваться ботом (Telegram user id через запятую/пробел).
    # Пусто = доступ открыт всем (НЕ рекомендуется в проде).
    allowed_user_ids: set[int] = field(
        default_factory=lambda: _parse_ids(os.getenv("ALLOWED_USER_IDS", ""))
    )

    def validate(self) -> None:
        missing = []
        if not self.bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.gdrive_folder_id:
            missing.append("GDRIVE_FOLDER_ID")
        if not Path(self.gdrive_service_account_file).exists():
            missing.append(f"{self.gdrive_service_account_file} (файл сервисного аккаунта)")
        if missing:
            raise RuntimeError(
                "Не настроено окружение, отсутствует: " + ", ".join(missing)
            )


settings = Settings()

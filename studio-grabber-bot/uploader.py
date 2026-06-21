"""Загрузка файлов в Google Drive и получение ссылки на скачивание."""
import datetime as dt
import logging
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import settings

logger = logging.getLogger("studio-grabber.uploader")

SCOPES = ["https://www.googleapis.com/auth/drive"]


class UploadError(Exception):
    pass


def _service():
    creds = service_account.Credentials.from_service_account_file(
        settings.gdrive_service_account_file, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _ensure_folder(service, name: str, parent_id: str) -> str:
    """Находит или создаёт подпапку `name` внутри `parent_id`, возвращает её id."""
    safe = name.replace("'", "\\'")
    query = (
        f"name = '{safe}' and '{parent_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    resp = (
        service.files()
        .list(q=query, fields="files(id)", supportsAllDrives=True,
              includeItemsFromAllDrives=True)
        .execute()
    )
    items = resp.get("files", [])
    if items:
        return items[0]["id"]
    folder = (
        service.files()
        .create(
            body={
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            },
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )
    return folder["id"]


def upload_file(path: Path) -> str:
    """Заливает файл в Drive и возвращает ссылку (webViewLink)."""
    try:
        service = _service()
        parent = settings.gdrive_folder_id
        if settings.date_subfolders:
            today = dt.date.today().isoformat()  # ГГГГ-ММ-ДД
            parent = _ensure_folder(service, today, parent)

        media = MediaFileUpload(str(path), resumable=True)
        created = (
            service.files()
            .create(
                body={"name": path.name, "parents": [parent]},
                media_body=media,
                fields="id, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )

        if settings.make_public:
            service.permissions().create(
                fileId=created["id"],
                body={"role": "reader", "type": "anyone"},
                supportsAllDrives=True,
            ).execute()

        return created.get("webViewLink", f"https://drive.google.com/file/d/{created['id']}/view")
    except Exception as exc:  # noqa: BLE001
        raise UploadError(str(exc)) from exc

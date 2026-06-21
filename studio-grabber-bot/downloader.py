"""Скачивание медиа в максимальном качестве.

Стратегия выбора движка:
  1. yt-dlp  — видео/аудио (YouTube, TikTok, Vimeo, видео из Instagram и т.д.)
  2. gallery-dl — фото/галереи (посты и карусели Instagram, X/Twitter, Pinterest)

Сначала пробуем yt-dlp; если он ничего не отдал — fallback на gallery-dl.
"""
import logging
import subprocess
from pathlib import Path

import yt_dlp

logger = logging.getLogger("studio-grabber.downloader")


class DownloadError(Exception):
    pass


def _new_files(dest: Path, before: set[Path]) -> list[Path]:
    return sorted(
        p for p in dest.glob("**/*") if p.is_file() and p not in before
    )


def _ytdlp_download(url: str, dest: Path) -> list[Path]:
    before = set(dest.glob("**/*"))
    ydl_opts = {
        # Лучшее видео + лучшее аудио, склейка в mp4
        "format": "bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": str(dest / "%(title).80B [%(id)s].%(ext)s"),
        "restrictfilenames": True,
        "noplaylist": False,
        "concurrent_fragment_downloads": 4,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return _new_files(dest, before)


def _gallerydl_download(url: str, dest: Path) -> list[Path]:
    before = set(dest.glob("**/*"))
    proc = subprocess.run(
        ["gallery-dl", "--dest", str(dest), url],
        capture_output=True,
        text=True,
        timeout=60 * 30,
    )
    files = _new_files(dest, before)
    if not files and proc.returncode != 0:
        raise DownloadError(
            (proc.stderr or proc.stdout or "gallery-dl завершился с ошибкой").strip()
        )
    return files


def download_media(url: str, dest: Path) -> list[Path]:
    """Скачивает медиа по ссылке. Возвращает список путей к файлам."""
    dest.mkdir(parents=True, exist_ok=True)

    try:
        files = _ytdlp_download(url, dest)
        if files:
            logger.info("yt-dlp: скачано %d файл(ов)", len(files))
            return files
        logger.info("yt-dlp не нашёл видео, пробую gallery-dl")
    except Exception as exc:  # noqa: BLE001 — fallback ниже
        logger.warning("yt-dlp не справился (%s), пробую gallery-dl", exc)

    files = _gallerydl_download(url, dest)
    if not files:
        raise DownloadError("По этой ссылке не удалось найти медиа для скачивания.")
    logger.info("gallery-dl: скачано %d файл(ов)", len(files))
    return files

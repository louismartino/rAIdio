import logging
from datetime import date

import edge_tts
from telegram import Bot

from .config import NEWSLETTERS_DIR, THUMBNAIL_PATH, Settings

logger = logging.getLogger(__name__)

AUDIO_CAPTION = "Here are today's newsletters!"
AUDIO_TITLE_TEMPLATE = "Morning Radio — {date}"


async def send_text_message(settings: Settings, text: str) -> None:
    """Send a plain text message via Telegram."""
    bot = Bot(token=settings.telegram_token.get_secret_value())
    logger.info("Sending text message via Telegram...")
    await bot.send_message(chat_id=settings.telegram_chat_id, text=text)
    logger.info("Text message sent successfully.")


async def send_audio_message(settings: Settings, text: str, target_date: date) -> None:
    """Synthesize speech and send the audio file via Telegram."""
    logger.info("Generating audio and sending via Telegram...")

    date_str = target_date.strftime("%d_%m_%Y")
    filename = f"newsletters_{date_str}.mp3"

    NEWSLETTERS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = NEWSLETTERS_DIR / filename

    communicate = edge_tts.Communicate(text, settings.tts_voice, rate=settings.tts_rate)
    await communicate.save(str(file_path))

    bot = Bot(token=settings.telegram_token.get_secret_value())
    logger.info("Sending audio via Telegram...")

    with open(file_path, "rb") as audio:
        if THUMBNAIL_PATH.exists():
            with open(THUMBNAIL_PATH, "rb") as thumbnail:
                await bot.send_audio(
                    chat_id=settings.telegram_chat_id,
                    audio=audio,
                    title=AUDIO_TITLE_TEMPLATE.format(date=date_str),
                    performer="rAIdio",
                    thumbnail=thumbnail,
                    caption=AUDIO_CAPTION,
                )
        else:
            await bot.send_audio(
                chat_id=settings.telegram_chat_id,
                audio=audio,
                title=AUDIO_TITLE_TEMPLATE.format(date=date_str),
                performer="rAIdio",
                caption=AUDIO_CAPTION,
            )

    logger.info("Audio message sent successfully.")

import logging

from deep_translator import GoogleTranslator

from app.config import DEFAULT_LANGUAGE_CODE, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)


def translate_text(text: str, dest: str = DEFAULT_LANGUAGE_CODE, source: str = "auto") -> str:
    cleaned_text = text.strip()
    if not cleaned_text:
        return cleaned_text

    if dest not in SUPPORTED_LANGUAGES:
        logger.warning("Unsupported translation target '%s'. Falling back to English.", dest)
        dest = DEFAULT_LANGUAGE_CODE

    try:
        translator = GoogleTranslator(source=source, target=dest)
        return translator.translate(cleaned_text) or cleaned_text
    except Exception as exc:
        logger.warning("Translation failed for source '%s' and destination '%s': %s", source, dest, exc)
        return cleaned_text

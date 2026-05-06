from typing import Dict

from langdetect import DetectorFactory, detect, detect_langs

from app.config import DEFAULT_LANGUAGE_CODE, SUPPORTED_LANGUAGES

DetectorFactory.seed = 0


def detect_language(text: str) -> Dict[str, str]:
    cleaned_text = text.strip()
    if not cleaned_text:
        return {
            "code": DEFAULT_LANGUAGE_CODE,
            "name": SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE_CODE],
            "confidence": "1.0",
        }

    try:
        probabilities = detect_langs(cleaned_text)
        best_guess = probabilities[0]
        lang_code = best_guess.lang
        confidence = f"{best_guess.prob:.2f}"
    except Exception:
        try:
            lang_code = detect(cleaned_text)
        except Exception:
            lang_code = DEFAULT_LANGUAGE_CODE
        confidence = "0.00"

    if lang_code not in SUPPORTED_LANGUAGES:
        lang_code = DEFAULT_LANGUAGE_CODE

    return {
        "code": lang_code,
        "name": SUPPORTED_LANGUAGES[lang_code],
        "confidence": confidence,
    }

from langdetect import detect


def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return "ar" if lang == "ar" else "en"
    except Exception:
        return "en"

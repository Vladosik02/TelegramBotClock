from . import uk, ru


def t(key: str, lang: str = "uk", **kwargs) -> str:
    strings = uk.STRINGS if lang == "uk" else ru.STRINGS
    text = strings.get(key, f"[{key}]")
    return text.format(**kwargs) if kwargs else text


LANG_NAMES = {
    "uk": "🇺🇦 Українська",
    "ru": "🇷🇺 Русский",
}

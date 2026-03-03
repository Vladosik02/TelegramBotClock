import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]
DB_PATH: str = os.getenv("DB_PATH", "clock.db")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env file")

# Booking zones: (zone_id, label_uk, label_ru)
ZONES: list[tuple[str, str, str]] = [
    ("tables_1", "🃏 Стіл настолок №1",    "🃏 Стол настолок №1"),
    ("tables_2", "🃏 Стіл настолок №2",    "🃏 Стол настолок №2"),
    ("ps5",      "🎮 PS5 диван",            "🎮 PS5 диван"),
    ("ps4",      "🎮 PS4 диван",            "🎮 PS4 диван"),
    ("vr",       "🥽 Oculus VR",            "🥽 Oculus VR"),
    ("hockey",   "🏒 Аерохокей",            "🏒 Аэрохоккей"),
    ("foosball", "⚽ Настільний футбол",    "⚽ Настольный футбол"),
]


def get_zone_label(zone_id: str, lang: str) -> str:
    for z in ZONES:
        if z[0] == zone_id:
            return z[1] if lang == "uk" else z[2]
    return zone_id


# ── Birthday ──
BIRTHDAY_DEPOSIT: int = 500          # Prepayment amount (грн)
BIRTHDAY_IBAN: str = ""              # TODO: вставте р/с (IBAN) сюди
BIRTHDAY_CLEANUP_MINUTES: int = 20   # Буфер прибирання після ДН (хвилин)
BIRTHDAY_RATE: int = 700             # грн/год для розрахунку балів ДН

# ── Points & Wallet ──
POINTS_PCT: int = 10                 # % від суми витрат → бали
REFERRAL_PCT: int = 3                # % від витрат реферала → реферерu бали
WALLET_BONUS_PCT: int = 5            # % бонусу при поповненні гаманця
WALLET_IBAN: str = "UA683220010000026005350066460"  # IBAN для поповнення гаманця
WALLET_TOPUP_TIMEOUT_MIN: int = 30   # хвилин до автоскасування заявки

# ── Bot ──
BOT_USERNAME: str = ""               # Ім'я бота (без @), для реферальних посилань. Встановіть вручну.

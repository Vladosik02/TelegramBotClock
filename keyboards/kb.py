import calendar as _calendar
from datetime import date as _date
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from locales import t
from config import ZONES


# ═══════════════════════════════════════════════════════════════
#  PERSISTENT REPLY KEYBOARD  (always visible at bottom)
# ═══════════════════════════════════════════════════════════════

def persistent_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Single '🏠 Меню' button always visible at the bottom."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🏠 Меню"))
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="🎮 Game Space Clock")


# ═══════════════════════════════════════════════════════════════
#  LANGUAGE
# ═══════════════════════════════════════════════════════════════

def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇦 Українська", callback_data="lang:uk")
    builder.button(text="RU  Русский",    callback_data="lang:ru")
    builder.adjust(2)
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════

def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_booking",      lang), callback_data="menu:booking")
    builder.button(text=t("btn_birthday",     lang), callback_data="menu:birthday")
    builder.button(text=t("btn_gallery",      lang), callback_data="menu:gallery")
    builder.button(text=t("btn_games",        lang), callback_data="menu:games")
    builder.button(text=t("btn_instructions", lang), callback_data="menu:instructions")
    builder.button(text=t("btn_suggestions",  lang), callback_data="menu:suggestions")
    builder.button(text=t("btn_bunker",       lang), callback_data="menu:bunker")
    builder.button(text=t("btn_profile",      lang), callback_data="menu:profile")
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════
#  UNIVERSAL NAV ROW  (reused by all section keyboards)
# ═══════════════════════════════════════════════════════════════

def _add_nav(builder: InlineKeyboardBuilder, lang: str, back_cb: str | None = None) -> None:
    """Append back + main-menu navigation row."""
    if back_cb:
        builder.button(text=t("btn_back", lang),      callback_data=back_cb)
    builder.button(text=t("btn_main_menu", lang), callback_data="menu:main")


def back_to_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _add_nav(builder, lang)
    return builder.as_markup()


def back_and_menu_keyboard(back_cb: str, lang: str) -> InlineKeyboardMarkup:
    """◀️ Back + 🏠 Main menu — two buttons in one row."""
    builder = InlineKeyboardBuilder()
    _add_nav(builder, lang, back_cb)
    builder.adjust(2)
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════
#  BOOKING / FORM
# ═══════════════════════════════════════════════════════════════

def cancel_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_cancel",    lang), callback_data="cancel")
    builder.button(text=t("btn_main_menu", lang), callback_data="menu:main")
    builder.adjust(2)
    return builder.as_markup()


def confirm_cancel_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_confirm", lang), callback_data="confirm")
    builder.button(text=t("btn_cancel",  lang), callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


def zones_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for zone_id, label_uk, label_ru in ZONES:
        label = label_uk if lang == "uk" else label_ru
        builder.button(text=label, callback_data=f"zone:{zone_id}")
    builder.button(text=t("btn_cancel",    lang), callback_data="cancel")
    builder.button(text=t("btn_main_menu", lang), callback_data="menu:main")
    builder.adjust(2, 2, 1, 2, 2)
    return builder.as_markup()


def payment_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("payment_iban", lang), callback_data="payment:iban")
    builder.button(text=t("payment_cash", lang), callback_data="payment:cash")
    builder.button(text=t("btn_cancel",   lang), callback_data="cancel")
    builder.button(text=t("btn_main_menu",lang), callback_data="menu:main")
    builder.adjust(1, 1, 2)
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════
#  GAMES
# ═══════════════════════════════════════════════════════════════

def games_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_ps5_games", lang), callback_data="games:PS5")
    builder.button(text=t("btn_ps4_games", lang), callback_data="games:PS4")
    _add_nav(builder, lang)
    builder.adjust(2, 2)
    return builder.as_markup()


def games_list_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Navigation for the game list page: back to games submenu + main menu."""
    builder = InlineKeyboardBuilder()
    _add_nav(builder, lang, back_cb="menu:games")
    builder.adjust(2)
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════
#  INSTRUCTIONS  (paginated, 5 per page)
# ═══════════════════════════════════════════════════════════════

_INSTR_PAGE_SIZE = 5


def instructions_list_keyboard(
    instructions: list[dict], lang: str, page: int = 0
) -> InlineKeyboardMarkup:
    total = len(instructions)
    total_pages = max(1, (total + _INSTR_PAGE_SIZE - 1) // _INSTR_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    start = page * _INSTR_PAGE_SIZE
    page_items = instructions[start : start + _INSTR_PAGE_SIZE]

    rows: list[list[InlineKeyboardButton]] = []

    for item in page_items:
        rows.append([InlineKeyboardButton(
            text=f"📖 {item['game_name']}",
            callback_data=f"instr:{item['id']}",
        )])

    # Pagination row — only when more than one page
    if total_pages > 1:
        pag: list[InlineKeyboardButton] = []
        if page > 0:
            pag.append(InlineKeyboardButton(text="◀️", callback_data=f"instr_page:{page - 1}"))
        pag.append(InlineKeyboardButton(text=f"{page + 1} / {total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            pag.append(InlineKeyboardButton(text="▶️", callback_data=f"instr_page:{page + 1}"))
        rows.append(pag)

    # Nav row — main menu only (instructions is top-level)
    rows.append([InlineKeyboardButton(
        text=t("btn_main_menu", lang), callback_data="menu:main",
    )])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def instruction_back_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _add_nav(builder, lang, back_cb="menu:instructions")
    builder.adjust(2)
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════
#  BIRTHDAY CALENDAR
# ═══════════════════════════════════════════════════════════════

_MONTH_NAMES_UK = [
    "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
    "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень",
]
_MONTH_NAMES_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]


def birthday_calendar_keyboard(
    year: int, month: int, booked_dates: set[str], lang: str
) -> InlineKeyboardMarkup:
    """Month grid calendar for birthday date selection.
    Booked dates shown as 🔴, past dates as ·, free dates as day number.
    """
    today = _date.today()
    month_names = _MONTH_NAMES_UK if lang == "uk" else _MONTH_NAMES_RU
    month_label = f"{month_names[month - 1]} {year}"

    # Prev/next month values
    if month == 1:
        prev_y, prev_m = year - 1, 12
    else:
        prev_y, prev_m = year, month - 1
    if month == 12:
        next_y, next_m = year + 1, 1
    else:
        next_y, next_m = year, month + 1

    rows: list[list[InlineKeyboardButton]] = []

    # Row 1: ◀ Month Year ▶
    can_go_prev = (prev_y, prev_m) >= (today.year, today.month)
    rows.append([
        InlineKeyboardButton(
            text="◀️",
            callback_data=f"bday_cal:{prev_y}:{prev_m}" if can_go_prev else "noop",
        ),
        InlineKeyboardButton(text=month_label, callback_data="noop"),
        InlineKeyboardButton(text="▶️", callback_data=f"bday_cal:{next_y}:{next_m}"),
    ])

    # Row 2: weekday headers Mon–Sun
    rows.append([InlineKeyboardButton(text=d, callback_data="noop") for d in _WEEKDAYS])

    # Calendar day rows
    for week in _calendar.monthcalendar(year, month):
        row: list[InlineKeyboardButton] = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="noop"))
            else:
                d = _date(year, month, day)
                date_str = d.strftime("%Y-%m-%d")
                if d < today:
                    row.append(InlineKeyboardButton(text="·", callback_data="noop"))
                elif date_str in booked_dates:
                    row.append(InlineKeyboardButton(text="🔴", callback_data="noop"))
                else:
                    row.append(InlineKeyboardButton(
                        text=str(day), callback_data=f"bday_date:{date_str}",
                    ))
        rows.append(row)

    # Last row: Cancel + Main menu
    rows.append([
        InlineKeyboardButton(text=t("btn_cancel",    lang), callback_data="cancel"),
        InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  BIRTHDAY — TIME PICKER
# ═══════════════════════════════════════════════════════════════

_BDAY_TIMES = [
    ("☀️ 13:00", "13:00"), ("☀️ 14:00", "14:00"), ("☀️ 15:00", "15:00"), ("☀️ 16:00", "16:00"),
    ("☀️ 17:00", "17:00"), ("🌙 18:00", "18:00"), ("🌙 19:00", "19:00"), ("🌙 20:00", "20:00"),
    ("🌙 21:00", "21:00"), ("🌙 22:00", "22:00"), ("🌙 23:00", "23:00"),
]


def calc_blocked_start_times(blocks: list[tuple[int, int]]) -> set[str]:
    """Return set of time strings (e.g. '13:00') that fall inside any existing birthday block.
    Used to filter the start-time picker.
    """
    skip: set[str] = set()
    for _, value in _BDAY_TIMES:
        h, m = int(value[:2]), int(value[3:])
        t_min = h * 60 + m
        if any(b_s <= t_min < b_e for b_s, b_e in blocks):
            skip.add(value)
    return skip


def calc_blocked_end_times(start_min: int, blocks: list[tuple[int, int]], cleanup: int) -> set[str]:
    """Return set of time strings that would cause the new birthday [start_min, e+cleanup)
    to overlap an existing block. Used to filter the end-time picker.
    """
    skip: set[str] = set()
    for _, value in _BDAY_TIMES:
        h, m = int(value[:2]), int(value[3:])
        e_min = h * 60 + m
        for b_s, b_e in blocks:
            if start_min < b_e and b_s < e_min + cleanup:
                skip.add(value)
                break
    return skip


def birthday_time_keyboard(
    lang: str,
    after: str = "",
    skip_times: set[str] | None = None,
) -> InlineKeyboardMarkup:
    """Grid of time slots: 4 columns, ☀️ day / 🌙 evening emojis.
    If `after` is set (e.g. '14:00'), only slots strictly after that time are shown.
    If `skip_times` is set, those specific slot values are hidden (already booked).
    """
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for label, value in _BDAY_TIMES:
        if after and value <= after:
            continue
        if skip_times and value in skip_times:
            continue
        row.append(InlineKeyboardButton(text=label, callback_data=f"bday_time:{value}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text=t("btn_cancel",    lang), callback_data="cancel"),
        InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  BIRTHDAY — GENDER PICKER  (age-conditional)
# ═══════════════════════════════════════════════════════════════

def birthday_gender_keyboard(age: int, lang: str) -> InlineKeyboardMarkup:
    """Return gender keyboard based on age group.
    6–14  → Boy / Girl / Skip
    15+   → Man / Woman / Skip
    """
    rows: list[list[InlineKeyboardButton]] = []
    if 6 <= age <= 14:
        rows.append([
            InlineKeyboardButton(text=t("bday_btn_boy",  lang), callback_data="bday_gender:boy"),
            InlineKeyboardButton(text=t("bday_btn_girl", lang), callback_data="bday_gender:girl"),
        ])
    else:  # 15+
        rows.append([
            InlineKeyboardButton(text=t("bday_btn_man",   lang), callback_data="bday_gender:man"),
            InlineKeyboardButton(text=t("bday_btn_woman", lang), callback_data="bday_gender:woman"),
        ])
    rows.append([
        InlineKeyboardButton(text=t("bday_btn_skip", lang), callback_data="bday_gender:skip"),
    ])
    rows.append([
        InlineKeyboardButton(text=t("btn_cancel",    lang), callback_data="cancel"),
        InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  BIRTHDAY — PAYMENT PICKER
# ═══════════════════════════════════════════════════════════════

def birthday_payment_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=t("bday_btn_iban", lang), callback_data="bday_pay:iban")],
        [InlineKeyboardButton(text=t("bday_btn_cash", lang), callback_data="bday_pay:cash")],
        [
            InlineKeyboardButton(text=t("btn_cancel",    lang), callback_data="cancel"),
            InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  BOOKING — CALENDAR + TIME PICKER
# ═══════════════════════════════════════════════════════════════

# 30-minute slots: 13:00, 13:30, …, 22:30, 23:00  (21 entries)
_BOOKING_SLOTS: list[tuple[str, str]] = []
for _bh in range(13, 24):
    _emoji = "☀️" if _bh < 18 else "🌙"
    _BOOKING_SLOTS.append((f"{_emoji} {_bh:02d}:00", f"{_bh:02d}:00"))
    if _bh < 23:
        _BOOKING_SLOTS.append((f"{_emoji} {_bh:02d}:30", f"{_bh:02d}:30"))


def booking_calendar_keyboard(
    year: int,
    month: int,
    date_statuses: dict,   # {date_iso: 'partial'|'full'}
    zone_id: str,
    lang: str,
) -> InlineKeyboardMarkup:
    """Month-grid calendar for booking date selection.
    🔴 = fully booked (noop).  🟡N = partial — some free slots (clickable).
    N  = fully free (clickable).  · = past day.
    """
    today = _date.today()
    month_names = _MONTH_NAMES_UK if lang == "uk" else _MONTH_NAMES_RU
    month_label = f"{month_names[month - 1]} {year}"

    if month == 1:
        prev_y, prev_m = year - 1, 12
    else:
        prev_y, prev_m = year, month - 1
    if month == 12:
        next_y, next_m = year + 1, 1
    else:
        next_y, next_m = year, month + 1

    rows: list[list[InlineKeyboardButton]] = []

    can_go_prev = (prev_y, prev_m) >= (today.year, today.month)
    rows.append([
        InlineKeyboardButton(
            text="◀️",
            callback_data=f"book_cal:{zone_id}:{prev_y}:{prev_m}" if can_go_prev else "noop",
        ),
        InlineKeyboardButton(text=month_label, callback_data="noop"),
        InlineKeyboardButton(text="▶️", callback_data=f"book_cal:{zone_id}:{next_y}:{next_m}"),
    ])

    rows.append([InlineKeyboardButton(text=d, callback_data="noop") for d in _WEEKDAYS])

    for week in _calendar.monthcalendar(year, month):
        row: list[InlineKeyboardButton] = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="noop"))
            else:
                d = _date(year, month, day)
                date_str = d.strftime("%Y-%m-%d")
                if d < today:
                    row.append(InlineKeyboardButton(text="·", callback_data="noop"))
                else:
                    status = date_statuses.get(date_str)
                    if status == "full":
                        row.append(InlineKeyboardButton(text="🔴", callback_data="noop"))
                    elif status == "partial":
                        row.append(InlineKeyboardButton(
                            text=f"🟡{day}",
                            callback_data=f"book_date:{date_str}",
                        ))
                    else:
                        row.append(InlineKeyboardButton(
                            text=str(day),
                            callback_data=f"book_date:{date_str}",
                        ))
        rows.append(row)

    rows.append([
        InlineKeyboardButton(text=t("btn_cancel",    lang), callback_data="cancel"),
        InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def calc_booking_blocked_start_times(blocks: list[tuple[int, int]]) -> set[str]:
    """Return set of start-time values (e.g. '14:30') that fall inside an existing block."""
    skip: set[str] = set()
    for _, value in _BOOKING_SLOTS:
        h, m = int(value[:2]), int(value[3:])
        t_min = h * 60 + m
        if t_min > 22 * 60 + 30:          # 23:00 is not a valid start slot
            continue
        if any(b_s <= t_min < b_e for b_s, b_e in blocks):
            skip.add(value)
    return skip


def calc_booking_blocked_end_times(
    start_min: int, blocks: list[tuple[int, int]]
) -> set[str]:
    """Return set of end-time values that would cause overlap with existing blocks."""
    skip: set[str] = set()
    for _, value in _BOOKING_SLOTS:
        h, m = int(value[:2]), int(value[3:])
        e_min = h * 60 + m
        if e_min - start_min < 30:
            continue   # already filtered by minimum duration — skip anyway
        for b_s, b_e in blocks:
            # [start_min, e_min) overlaps [b_s, b_e)?
            if start_min < b_e and b_s < e_min:
                skip.add(value)
                break
    return skip


def booking_time_keyboard(
    lang: str,
    start_value: str = "",           # empty → start picker; set → end picker
    skip_times: set[str] | None = None,
) -> InlineKeyboardMarkup:
    """Start or end time picker for booking (30-minute slots).
    Start picker: 13:00 – 22:30 (max start so that ≥30 min remains before 23:00).
    End   picker: start_value+30min – 23:00.
    Buttons blocked by skip_times are hidden entirely.
    """
    rows: list[list[InlineKeyboardButton]] = []
    row:  list[InlineKeyboardButton] = []

    start_min = 0
    if start_value:
        sh, sm = int(start_value[:2]), int(start_value[3:])
        start_min = sh * 60 + sm

    for label, value in _BOOKING_SLOTS:
        vh, vm = int(value[:2]), int(value[3:])
        v_min = vh * 60 + vm

        if not start_value:
            # Start picker: latest valid start is 22:30 (23:00 - 30min)
            if v_min > 22 * 60 + 30:
                continue
        else:
            # End picker: must be ≥30 min after start
            if v_min - start_min < 30:
                continue

        if skip_times and value in skip_times:
            continue

        row.append(InlineKeyboardButton(text=label, callback_data=f"book_time:{value}"))
        if len(row) == 4:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append([
        InlineKeyboardButton(text=t("btn_cancel",    lang), callback_data="cancel"),
        InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  GALLERY
# ═══════════════════════════════════════════════════════════════

def gallery_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _add_nav(builder, lang)
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════
#  PROFILE
# ═══════════════════════════════════════════════════════════════

def profile_keyboard(
    lang: str,
    saved_name: str = "",
    saved_phone: str = "",
    points: int = 0,
    wallet: int = 0,
) -> InlineKeyboardMarkup:
    name_label  = saved_name  or t("profile_name_not_set",  lang)
    phone_label = saved_phone or t("profile_phone_not_set", lang)
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(
            text=t("btn_edit_name",  lang).format(name=name_label),
            callback_data="profile:edit_name",
        )],
        [InlineKeyboardButton(
            text=t("btn_edit_phone", lang).format(phone=phone_label),
            callback_data="profile:edit_phone",
        )],
        [
            InlineKeyboardButton(
                text=t("btn_points", lang).format(points=points),
                callback_data="profile:points",
            ),
            InlineKeyboardButton(
                text=t("btn_wallet", lang).format(wallet=wallet),
                callback_data="profile:wallet",
            ),
        ],
        [InlineKeyboardButton(
            text=t("btn_referrals",   lang), callback_data="profile:referrals",
        )],
        [InlineKeyboardButton(
            text=t("btn_change_lang", lang), callback_data="menu:lang_change",
        )],
        [InlineKeyboardButton(
            text=t("btn_main_menu",   lang), callback_data="menu:main",
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def use_saved_name_keyboard(name: str, lang: str, prefix: str = "booking") -> InlineKeyboardMarkup:
    """'✅ Use: Name' + '✏️ Other name' + cancel row."""
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(
            text=t("btn_use_saved_name", lang).format(name=name),
            callback_data=f"{prefix}:use_name",
        )],
        [InlineKeyboardButton(
            text=t("btn_enter_other_name", lang),
            callback_data=f"{prefix}:enter_name",
        )],
        [
            InlineKeyboardButton(text=t("btn_cancel",    lang), callback_data="cancel"),
            InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def use_saved_phone_keyboard(phone: str, lang: str, prefix: str = "booking") -> InlineKeyboardMarkup:
    """'✅ Use: Phone' + '✏️ Other phone' + cancel row."""
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(
            text=t("btn_use_saved_phone", lang).format(phone=phone),
            callback_data=f"{prefix}:use_phone",
        )],
        [InlineKeyboardButton(
            text=t("btn_enter_other_phone", lang),
            callback_data=f"{prefix}:enter_phone",
        )],
        [
            InlineKeyboardButton(text=t("btn_cancel",    lang), callback_data="cancel"),
            InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def points_history_keyboard(page: int, total_pages: int, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if total_pages > 1:
        pag: list[InlineKeyboardButton] = []
        if page > 0:
            pag.append(InlineKeyboardButton(text="◀️", callback_data=f"profile:points_page:{page - 1}"))
        pag.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            pag.append(InlineKeyboardButton(text="▶️", callback_data=f"profile:points_page:{page + 1}"))
        rows.append(pag)
    rows.append([
        InlineKeyboardButton(text=t("btn_back",      lang), callback_data="profile:main"),
        InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def wallet_keyboard(wallet: int, bonus_pct: int, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(
            text=t("wallet_topup_btn", lang), callback_data="profile:wallet_topup",
        )],
        [InlineKeyboardButton(
            text=t("wallet_history_btn", lang), callback_data="profile:wallet_history",
        )],
        [
            InlineKeyboardButton(text=t("btn_back",      lang), callback_data="profile:main"),
            InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def referrals_keyboard(lang: str, has_referrer: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if not has_referrer:
        rows.append([InlineKeyboardButton(
            text=t("btn_enter_ref_code", lang), callback_data="profile:enter_ref",
        )])
    rows.append([
        InlineKeyboardButton(text=t("btn_back",      lang), callback_data="profile:main"),
        InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  ADMIN
# ═══════════════════════════════════════════════════════════════

def admin_panel_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_bookings_list",   lang), callback_data="admin:bookings:0")
    builder.button(text=t("btn_birthday_list",   lang), callback_data="admin:birthdays:0")
    builder.button(text=t("btn_stats",           lang), callback_data="admin:stats")
    builder.button(text=t("btn_add_booking",     lang), callback_data="admin:add_booking")
    builder.button(text=t("btn_users",           lang), callback_data="admin:users:0")
    builder.button(text=t("btn_broadcast",       lang), callback_data="admin:broadcast")
    builder.button(text=t("btn_wallet_topups",   lang), callback_data="admin:topups")
    builder.button(text=t("btn_ref_bonuses",     lang), callback_data="admin:ref_bonuses")
    builder.button(text=t("btn_add_game",        lang), callback_data="admin:add_game")
    builder.button(text=t("btn_add_photo",       lang), callback_data="admin:add_photo")
    builder.button(text=t("btn_add_instruction", lang), callback_data="admin:add_instruction")
    _add_nav(builder, lang)
    builder.adjust(2, 2, 2, 2, 3, 1)
    return builder.as_markup()


def admin_platform_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 PS5", callback_data="platform:PS5")
    builder.button(text="🕹 PS4", callback_data="platform:PS4")
    builder.adjust(2)
    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════
#  ADMIN — BOOKINGS LIST (paginated)
# ═══════════════════════════════════════════════════════════════

_ADMIN_PAGE_SIZE = 8


def _status_badge(status: str) -> str:
    return {"pending": "🕐", "confirmed": "✅", "cancelled": "❌"}.get(status, "❓")


def admin_bookings_list_keyboard(
    bookings: list[dict], lang: str, page: int
) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(bookings) + _ADMIN_PAGE_SIZE - 1) // _ADMIN_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    page_items = bookings[page * _ADMIN_PAGE_SIZE: (page + 1) * _ADMIN_PAGE_SIZE]

    rows: list[list[InlineKeyboardButton]] = []
    for b in page_items:
        badge = _status_badge(b["status"])
        label = f"{badge} #{b['id']} {b['booking_date']} | {b['zone']} | {b['user_name'] or '—'}"
        rows.append([InlineKeyboardButton(
            text=label[:50], callback_data=f"admin:booking:{b['id']}",
        )])

    if total_pages > 1:
        pag: list[InlineKeyboardButton] = []
        if page > 0:
            pag.append(InlineKeyboardButton(text="◀️", callback_data=f"admin:bookings:{page - 1}"))
        pag.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            pag.append(InlineKeyboardButton(text="▶️", callback_data=f"admin:bookings:{page + 1}"))
        rows.append(pag)

    rows.append([
        InlineKeyboardButton(text=t("btn_add_booking", lang),  callback_data="admin:add_booking"),
        InlineKeyboardButton(text=t("btn_admin_panel", lang),  callback_data="admin:panel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_booking_detail_keyboard(
    booking_id: int, status: str, lang: str
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status == "pending":
        rows.append([
            InlineKeyboardButton(
                text=t("btn_confirm_booking", lang),
                callback_data=f"admin:booking_confirm:{booking_id}",
            ),
            InlineKeyboardButton(
                text=t("btn_cancel_booking", lang),
                callback_data=f"admin:booking_cancel:{booking_id}",
            ),
        ])
    elif status == "confirmed":
        rows.append([InlineKeyboardButton(
            text=t("btn_cancel_booking", lang),
            callback_data=f"admin:booking_cancel:{booking_id}",
        )])
    elif status == "cancelled":
        rows.append([InlineKeyboardButton(
            text=t("btn_delete_entry", lang),
            callback_data=f"admin:booking_delete:{booking_id}",
        )])
    rows.append([
        InlineKeyboardButton(text=t("btn_back",       lang), callback_data="admin:bookings:0"),
        InlineKeyboardButton(text=t("btn_admin_panel", lang), callback_data="admin:panel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  ADMIN — BIRTHDAY ORDERS LIST (paginated)
# ═══════════════════════════════════════════════════════════════

def admin_birthdays_list_keyboard(
    orders: list[dict], lang: str, page: int
) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(orders) + _ADMIN_PAGE_SIZE - 1) // _ADMIN_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    page_items = orders[page * _ADMIN_PAGE_SIZE: (page + 1) * _ADMIN_PAGE_SIZE]

    rows: list[list[InlineKeyboardButton]] = []
    for o in page_items:
        badge = _status_badge(o["status"])
        label = f"{badge} #{o['id']} {o['birthday_date']} | {o['contact_name'] or '—'} | {o['guests_count'] or '?'} ос."
        rows.append([InlineKeyboardButton(
            text=label[:50], callback_data=f"admin:birthday:{o['id']}",
        )])

    if total_pages > 1:
        pag: list[InlineKeyboardButton] = []
        if page > 0:
            pag.append(InlineKeyboardButton(text="◀️", callback_data=f"admin:birthdays:{page - 1}"))
        pag.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            pag.append(InlineKeyboardButton(text="▶️", callback_data=f"admin:birthdays:{page + 1}"))
        rows.append(pag)

    rows.append([InlineKeyboardButton(
        text=t("btn_admin_panel", lang), callback_data="admin:panel",
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_birthday_detail_keyboard(
    order_id: int, status: str, lang: str
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status == "pending":
        rows.append([
            InlineKeyboardButton(
                text=t("btn_confirm_booking", lang),
                callback_data=f"admin:birthday_confirm:{order_id}",
            ),
            InlineKeyboardButton(
                text=t("btn_cancel_booking", lang),
                callback_data=f"admin:birthday_cancel:{order_id}",
            ),
        ])
    elif status == "confirmed":
        rows.append([InlineKeyboardButton(
            text=t("btn_cancel_booking", lang),
            callback_data=f"admin:birthday_cancel:{order_id}",
        )])
    elif status == "cancelled":
        rows.append([InlineKeyboardButton(
            text=t("btn_delete_entry", lang),
            callback_data=f"admin:birthday_delete:{order_id}",
        )])
    rows.append([
        InlineKeyboardButton(text=t("btn_back",       lang), callback_data="admin:birthdays:0"),
        InlineKeyboardButton(text=t("btn_admin_panel", lang), callback_data="admin:panel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  ADMIN — USERS LIST (paginated)
# ═══════════════════════════════════════════════════════════════

def admin_users_list_keyboard(
    users: list[dict], lang: str, page: int
) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(users) + _ADMIN_PAGE_SIZE - 1) // _ADMIN_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    page_items = users[page * _ADMIN_PAGE_SIZE: (page + 1) * _ADMIN_PAGE_SIZE]

    rows: list[list[InlineKeyboardButton]] = []
    for u in page_items:
        blocked = bool(u.get("is_blocked"))
        badge = "🔴" if blocked else "🟢"
        name = (u.get("full_name") or u.get("username") or "—")[:20]
        uname = f" @{u['username']}" if u.get("username") else ""
        rows.append([InlineKeyboardButton(
            text=f"{badge} {name}{uname}"[:48],
            callback_data=f"admin:user:{u['tg_id']}",
        )])

    if total_pages > 1:
        pag: list[InlineKeyboardButton] = []
        if page > 0:
            pag.append(InlineKeyboardButton(text="◀️", callback_data=f"admin:users:{page - 1}"))
        pag.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            pag.append(InlineKeyboardButton(text="▶️", callback_data=f"admin:users:{page + 1}"))
        rows.append(pag)

    rows.append([InlineKeyboardButton(
        text=t("btn_admin_panel", lang), callback_data="admin:panel",
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_user_detail_keyboard(
    tg_id: int, is_blocked_flag: bool, lang: str
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if is_blocked_flag:
        rows.append([InlineKeyboardButton(
            text=t("btn_unblock_user", lang),
            callback_data=f"admin:user_unblock:{tg_id}",
        )])
    else:
        rows.append([InlineKeyboardButton(
            text=t("btn_block_user", lang),
            callback_data=f"admin:user_block:{tg_id}",
        )])
    rows.append([
        InlineKeyboardButton(text=t("btn_back",       lang), callback_data="admin:users:0"),
        InlineKeyboardButton(text=t("btn_admin_panel", lang), callback_data="admin:panel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  ADMIN — MISC KEYBOARDS
# ═══════════════════════════════════════════════════════════════

def back_to_admin_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_admin_panel", lang), callback_data="admin:panel")
    return builder.as_markup()


def broadcast_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(
            text=t("btn_broadcast_send",  lang), callback_data="admin:broadcast_confirm",
        ),
        InlineKeyboardButton(
            text=t("btn_cancel",          lang), callback_data="admin:broadcast_cancel",
        ),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  ADMIN — WALLET TOPUPS
# ═══════════════════════════════════════════════════════════════

def admin_topups_list_keyboard(topups: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for tx in topups:
        label = f"#{tx['id']} · {tx['amount']} грн · {(tx.get('full_name') or tx.get('username') or str(tx['tg_id']))[:20]}"
        rows.append([InlineKeyboardButton(
            text=label[:50], callback_data=f"admin:topup:{tx['id']}",
        )])
    rows.append([InlineKeyboardButton(
        text=t("btn_admin_panel", lang), callback_data="admin:panel",
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_topup_detail_keyboard(tx_id: int, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(
            text=t("btn_confirm_topup", lang),
            callback_data=f"admin:topup_confirm:{tx_id}",
        )],
        [InlineKeyboardButton(
            text=t("btn_cancel_topup", lang),
            callback_data=f"admin:topup_cancel:{tx_id}",
        )],
        [
            InlineKeyboardButton(text=t("btn_back",       lang), callback_data="admin:topups"),
            InlineKeyboardButton(text=t("btn_admin_panel", lang), callback_data="admin:panel"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  ADMIN — REFERRAL BONUSES
# ═══════════════════════════════════════════════════════════════

def admin_ref_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=t("btn_ref_bonuses_confirm", lang),
                callback_data="admin:ref_bonuses_confirm",
            ),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="admin:panel"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  BUNKER GAME
# ═══════════════════════════════════════════════════════════════

_BUNKER_ATTR_ORDER = ["profession", "health", "hobby", "phobia", "baggage", "ability"]


def bunker_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("bunker_btn_create", lang), callback_data="bunker:create")
    builder.button(text=t("bunker_btn_join",   lang), callback_data="bunker:join")
    builder.button(text=t("bunker_btn_rules",  lang), callback_data="bunker:rules")
    builder.button(text=t("btn_main_menu",     lang), callback_data="menu:main")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def bunker_player_count_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for n in range(4, 13):
        builder.button(text=str(n), callback_data=f"bunker:host_count:{n}")
    builder.button(text=t("btn_cancel", lang), callback_data="menu:main")
    builder.adjust(3, 3, 3, 1)
    return builder.as_markup()


def bunker_host_waiting_keyboard(session_id: int, joined: int, needed: int, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if joined >= needed:
        rows.append([InlineKeyboardButton(
            text=t("bunker_btn_start_game", lang),
            callback_data=f"bunker:start:{session_id}",
        )])
    rows.append([
        InlineKeyboardButton(text=t("bunker_btn_cancel_session", lang), callback_data=f"bunker:cancel:{session_id}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bunker_host_game_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("bunker_btn_reveal_round", lang), callback_data=f"bunker:round_open:{session_id}")
    builder.button(text=t("bunker_btn_draw_event",   lang), callback_data=f"bunker:draw_event:{session_id}")
    builder.button(text=t("bunker_btn_vote",         lang), callback_data=f"bunker:vote_start:{session_id}")
    builder.button(text=t("bunker_btn_end_game",     lang), callback_data=f"bunker:end:{session_id}")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def bunker_event_roll_keyboard(session_id: int, event_id: int, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("bunker_btn_roll_dice", lang),
        callback_data=f"bunker:roll_dice:{session_id}:{event_id}",
    )
    return builder.as_markup()


def bunker_steal_victim_keyboard(
    session_id: int, event_id: int, alive_players: list[dict], lang: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in alive_players:
        builder.button(
            text=p["display_name"],
            callback_data=f"bunker:steal_victim:{session_id}:{event_id}:{p['tg_id']}",
        )
    builder.adjust(1)
    return builder.as_markup()


def bunker_steal_attr_keyboard(
    session_id: int, event_id: int, victim_tg_id: int, revealed: list[str], lang: str
) -> InlineKeyboardMarkup:
    _LABELS = {"profession": "💼", "health": "❤️", "hobby": "🎯",
               "phobia": "😨", "baggage": "🎒", "ability": "⚡"}
    builder = InlineKeyboardBuilder()
    for attr in _BUNKER_ATTR_ORDER:
        if attr in revealed:
            label = f"{_LABELS.get(attr, '')} {t(f'bunker_attr_{attr}', lang).split()[-1]}"
            builder.button(
                text=label,
                callback_data=f"bunker:steal_attr:{session_id}:{event_id}:{victim_tg_id}:{attr}",
            )
    builder.adjust(1)
    return builder.as_markup()


def bunker_player_card_keyboard(session_id: int, card: dict, revealed: list, lang: str) -> InlineKeyboardMarkup:
    """Player's interactive card: unrevealed attrs are tappable, revealed shown with value (inactive)."""
    rows = []
    for attr in _BUNKER_ATTR_ORDER:
        label = t(f"bunker_attr_{attr}", lang)
        if attr in revealed:
            value = card.get(attr, "—")
            rows.append([InlineKeyboardButton(
                text=f"✅ {label}: {value}",
                callback_data="noop",
            )])
        else:
            rows.append([InlineKeyboardButton(
                text=f"🔓 {label}",
                callback_data=f"bunker:pick_attr:{session_id}:{attr}",
            )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bunker_player_confirm_keyboard(session_id: int, attr: str, lang: str) -> InlineKeyboardMarkup:
    """Confirm reveal (announce aloud) or go back to choose a different attr."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("bunker_btn_confirm_reveal", lang),
        callback_data=f"bunker:confirm_attr:{session_id}:{attr}",
    )
    builder.button(
        text=t("bunker_btn_back_to_card", lang),
        callback_data=f"bunker:back_to_card:{session_id}",
    )
    builder.adjust(1, 1)
    return builder.as_markup()


def bunker_vote_keyboard(session_id: int, alive_players: list[dict], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in alive_players:
        builder.button(
            text=p["display_name"],
            callback_data=f"bunker:vote:{session_id}:{p['tg_id']}",
        )
    builder.adjust(1)
    return builder.as_markup()


def bunker_host_kick_keyboard(session_id: int, candidates: list[tuple[int, str, int]], lang: str) -> InlineKeyboardMarkup:
    """candidates = list of (tg_id, display_name, vote_count) sorted desc."""
    rows: list[list[InlineKeyboardButton]] = []
    for tg_id, name, votes in candidates:
        rows.append([InlineKeyboardButton(
            text=f"❌ {name} ({votes} гол.)",
            callback_data=f"bunker:kick:{session_id}:{tg_id}",
        )])
    rows.append([InlineKeyboardButton(
        text=t("bunker_btn_skip_kick", lang),
        callback_data=f"bunker:skip_kick:{session_id}",
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)

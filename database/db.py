import logging
import re as _re
import aiosqlite
from config import DB_PATH

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
    return _db


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None


# ─────────────────────────── INIT ───────────────────────────

async def init_db() -> None:
    db = await get_db()

    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id       INTEGER UNIQUE NOT NULL,
            username    TEXT,
            full_name   TEXT,
            lang        TEXT DEFAULT 'uk',
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            points      INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_tg_id   INTEGER NOT NULL,
            user_name    TEXT,
            user_phone   TEXT,
            zone         TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            people_count INTEGER DEFAULT 1,
            payment_type TEXT NOT NULL,
            notes        TEXT,
            status       TEXT DEFAULT 'pending',
            created_at   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS birthday_orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_tg_id   INTEGER NOT NULL,
            contact_name TEXT,
            contact_phone TEXT,
            birthday_date TEXT NOT NULL,
            guests_count  TEXT,
            wishes        TEXT,
            status        TEXT DEFAULT 'pending',
            created_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS suggestions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_tg_id INTEGER NOT NULL,
            text       TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS ps_games (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            platform     TEXT NOT NULL,
            title        TEXT NOT NULL,
            image_file_id TEXT,
            sort_order   INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS board_game_instructions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name    TEXT NOT NULL,
            content_type TEXT DEFAULT 'text',
            text_content TEXT,
            file_id      TEXT,
            sort_order   INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS gallery (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id    TEXT NOT NULL,
            caption    TEXT,
            category   TEXT DEFAULT 'general',
            sort_order INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS points_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id       INTEGER NOT NULL,
            type        TEXT NOT NULL,
            amount      INTEGER NOT NULL,
            description TEXT,
            ref_id      INTEGER,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id       INTEGER NOT NULL,
            type        TEXT NOT NULL DEFAULT 'topup',
            amount      INTEGER NOT NULL,
            bonus       INTEGER DEFAULT 0,
            status      TEXT DEFAULT 'pending',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS bunker_sessions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            code             TEXT UNIQUE NOT NULL,
            host_tg_id       INTEGER NOT NULL,
            status           TEXT DEFAULT 'waiting',
            max_players      INTEGER NOT NULL,
            bunker_capacity  INTEGER DEFAULT 0,
            catastrophe_text TEXT DEFAULT '',
            bunker_text      TEXT DEFAULT '',
            current_attr     TEXT DEFAULT '',
            vote_round       INTEGER DEFAULT 0,
            created_at       TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS bunker_players (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   INTEGER NOT NULL,
            tg_id        INTEGER NOT NULL,
            display_name TEXT DEFAULT '',
            card_json    TEXT DEFAULT '{}',
            revealed     TEXT DEFAULT '[]',
            is_alive     INTEGER DEFAULT 1,
            joined_at    TEXT DEFAULT (datetime('now')),
            UNIQUE(session_id, tg_id)
        );

        CREATE TABLE IF NOT EXISTS bunker_votes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   INTEGER NOT NULL,
            vote_round   INTEGER NOT NULL,
            voter_tg_id  INTEGER NOT NULL,
            target_tg_id INTEGER NOT NULL,
            created_at   TEXT DEFAULT (datetime('now')),
            UNIQUE(session_id, vote_round, voter_tg_id)
        );

        CREATE TABLE IF NOT EXISTS bunker_attributes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            type    TEXT NOT NULL,
            text_uk TEXT NOT NULL,
            text_ru TEXT
        );

        CREATE TABLE IF NOT EXISTS bunker_scenarios (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            type         TEXT NOT NULL,
            text_uk      TEXT NOT NULL,
            text_ru      TEXT,
            capacity_min INTEGER DEFAULT 2,
            capacity_max INTEGER DEFAULT 5
        );

        CREATE TABLE IF NOT EXISTS bunker_active_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER NOT NULL,
            event_code      TEXT NOT NULL,
            dc              INTEGER NOT NULL,
            executor_tg_id  INTEGER DEFAULT 0,
            modifier        INTEGER DEFAULT 0,
            is_auto         INTEGER DEFAULT 0,
            victim_tg_id    INTEGER DEFAULT 0,
            thief_tg_id     INTEGER DEFAULT 0,
            stolen_attr     TEXT DEFAULT '',
            roll_result     INTEGER DEFAULT 0,
            outcome         TEXT DEFAULT '',
            round_num       INTEGER DEFAULT 0,
            is_resolved     INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS bunker_player_statuses (
            session_id    INTEGER NOT NULL,
            tg_id         INTEGER NOT NULL,
            status        TEXT NOT NULL,
            expires_round INTEGER DEFAULT 0,
            PRIMARY KEY (session_id, tg_id)
        );
    """)
    await db.commit()

    # Migrations — safe to run repeatedly
    for sql in [
        "ALTER TABLE board_game_instructions ADD COLUMN local_image TEXT",
        # Birthday v2 columns
        "ALTER TABLE birthday_orders ADD COLUMN birthday_time TEXT",
        "ALTER TABLE birthday_orders ADD COLUMN celebrant_age TEXT",
        "ALTER TABLE birthday_orders ADD COLUMN celebrant_gender TEXT",
        "ALTER TABLE birthday_orders ADD COLUMN fav_color TEXT",
        "ALTER TABLE birthday_orders ADD COLUMN payment_type TEXT",
        # Birthday v3 — separate start/end for conflict detection
        "ALTER TABLE birthday_orders ADD COLUMN birthday_time_start TEXT",
        "ALTER TABLE birthday_orders ADD COLUMN birthday_time_end TEXT",
        # User blocking
        "ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0",
        # Phase 3 — Profile + Points + Wallet
        "ALTER TABLE users ADD COLUMN saved_name TEXT",
        "ALTER TABLE users ADD COLUMN saved_phone TEXT",
        "ALTER TABLE users ADD COLUMN wallet_balance INTEGER DEFAULT 0",
        "ALTER TABLE bookings ADD COLUMN price INTEGER DEFAULT 0",
        "ALTER TABLE birthday_orders ADD COLUMN price INTEGER DEFAULT 0",
        # Wallet comment for payment reference
        "ALTER TABLE wallet_transactions ADD COLUMN comment TEXT DEFAULT ''",
        # Phase 5 — Bunker events
        "ALTER TABLE bunker_sessions ADD COLUMN last_event_code TEXT DEFAULT ''",
        "ALTER TABLE bunker_sessions ADD COLUMN last_event_round INTEGER DEFAULT 0",
    ]:
        try:
            await db.execute(sql)
            await db.commit()
        except Exception:
            pass  # Column already exists

    logging.info("Database initialized")


# ─────────────────────────── USERS ───────────────────────────

async def get_or_create_user(tg_id: int, username: str | None, full_name: str) -> dict:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM users WHERE tg_id = ?", (tg_id,)
    )).fetchone()

    if row:
        # Update username/name in case they changed
        await db.execute(
            "UPDATE users SET username=?, full_name=? WHERE tg_id=?",
            (username, full_name, tg_id)
        )
        await db.commit()
        return dict(row)

    import random, string
    ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    await db.execute(
        "INSERT INTO users (tg_id, username, full_name, referral_code) VALUES (?, ?, ?, ?)",
        (tg_id, username, full_name, ref_code)
    )
    await db.commit()
    row = await (await db.execute(
        "SELECT * FROM users WHERE tg_id = ?", (tg_id,)
    )).fetchone()
    return dict(row)


async def get_user(tg_id: int) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM users WHERE tg_id = ?", (tg_id,)
    )).fetchone()
    return dict(row) if row else None


async def get_user_lang(tg_id: int) -> str:
    user = await get_user(tg_id)
    return user["lang"] if user else "uk"


async def set_user_lang(tg_id: int, lang: str) -> None:
    db = await get_db()
    await db.execute("UPDATE users SET lang=? WHERE tg_id=?", (lang, tg_id))
    await db.commit()


async def add_points(tg_id: int, amount: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE users SET points = points + ? WHERE tg_id = ?", (amount, tg_id)
    )
    await db.commit()


async def get_user_bookings(tg_id: int, limit: int = 5) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM bookings WHERE user_tg_id=? ORDER BY created_at DESC LIMIT ?",
        (tg_id, limit)
    )).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────── BOOKINGS ───────────────────────────

async def create_booking(
    user_tg_id: int,
    user_name: str,
    user_phone: str,
    zone: str,
    booking_date: str,
    booking_time: str,
    people_count: int,
    payment_type: str,
    notes: str = "",
    price: int = 0,
) -> int:
    db = await get_db()
    cur = await db.execute(
        """INSERT INTO bookings
           (user_tg_id, user_name, user_phone, zone, booking_date, booking_time,
            people_count, payment_type, notes, price)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_tg_id, user_name, user_phone, zone, booking_date,
         booking_time, people_count, payment_type, notes, price),
    )
    await db.commit()
    return cur.lastrowid


async def get_all_bookings(limit: int = 50) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM bookings ORDER BY created_at DESC LIMIT ?", (limit,)
    )).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────── BIRTHDAY ORDERS ───────────────────────────

async def create_birthday_order(
    user_tg_id: int,
    contact_name: str,
    contact_phone: str,
    birthday_date: str,
    birthday_time: str = "",
    birthday_time_start: str = "",
    birthday_time_end: str = "",
    celebrant_age: str = "",
    celebrant_gender: str = "",
    fav_color: str = "",
    payment_type: str = "",
    guests_count: str = "",
    wishes: str = "",
    price: int = 0,
) -> int:
    db = await get_db()
    cur = await db.execute(
        """INSERT INTO birthday_orders
           (user_tg_id, contact_name, contact_phone, birthday_date,
            birthday_time, birthday_time_start, birthday_time_end,
            celebrant_age, celebrant_gender, fav_color,
            payment_type, guests_count, wishes, price)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_tg_id, contact_name, contact_phone, birthday_date,
         birthday_time, birthday_time_start, birthday_time_end,
         celebrant_age, celebrant_gender, fav_color,
         payment_type, guests_count, wishes, price),
    )
    await db.commit()
    return cur.lastrowid


async def get_birthday_blocks_for_date(date_str: str) -> list[tuple[int, int]]:
    """Return list of (start_min, end_min_with_cleanup) for active birthdays on date_str (YYYY-MM-DD)."""
    from config import BIRTHDAY_CLEANUP_MINUTES
    db = await get_db()
    rows = await (await db.execute(
        """SELECT birthday_time_start, birthday_time_end
           FROM birthday_orders
           WHERE birthday_date = ? AND status NOT IN ('rejected', 'cancelled')
             AND birthday_time_start IS NOT NULL AND birthday_time_end IS NOT NULL
             AND birthday_time_start != '' AND birthday_time_end != ''""",
        (date_str,)
    )).fetchall()
    result = []
    for row in rows:
        try:
            sh, sm = map(int, row[0].split(":"))
            eh, em = map(int, row[1].split(":"))
            result.append((sh * 60 + sm, eh * 60 + em + BIRTHDAY_CLEANUP_MINUTES))
        except Exception:
            pass
    return result


# Slot minutes used for birthday time picker (13:00 – 23:00, hourly)
_BDAY_SLOT_MINS = [h * 60 for h in range(13, 24)]


async def get_fully_booked_birthday_dates() -> set[str]:
    """Return dates (YYYY-MM-DD) where NO valid (start, end) birthday slot is left."""
    from config import BIRTHDAY_CLEANUP_MINUTES
    db = await get_db()
    rows = await (await db.execute(
        """SELECT birthday_date, birthday_time_start, birthday_time_end
           FROM birthday_orders
           WHERE status NOT IN ('rejected', 'cancelled')
             AND birthday_time_start IS NOT NULL AND birthday_time_end IS NOT NULL
             AND birthday_time_start != '' AND birthday_time_end != ''"""
    )).fetchall()

    # Group blocks by date
    date_blocks: dict[str, list[tuple[int, int]]] = {}
    for row in rows:
        date_str, ts, te = row[0], row[1], row[2]
        try:
            sh, sm = map(int, ts.split(":"))
            eh, em = map(int, te.split(":"))
            s_min = sh * 60 + sm
            e_min = eh * 60 + em + BIRTHDAY_CLEANUP_MINUTES
            date_blocks.setdefault(date_str, []).append((s_min, e_min))
        except Exception:
            pass

    fully_booked: set[str] = set()
    for date_str, blocks in date_blocks.items():
        has_slot = False
        for s in _BDAY_SLOT_MINS:
            # Start time must not fall inside any existing block
            if any(b_s <= s < b_e for b_s, b_e in blocks):
                continue
            for e in _BDAY_SLOT_MINS:
                if e <= s:
                    continue
                # New footprint [s, e+cleanup) must not overlap any block
                if not any(s < b_e and b_s < e + BIRTHDAY_CLEANUP_MINUTES for b_s, b_e in blocks):
                    has_slot = True
                    break
            if has_slot:
                break
        if not has_slot:
            fully_booked.add(date_str)

    return fully_booked


async def get_all_birthday_orders(limit: int = 50) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM birthday_orders ORDER BY created_at DESC LIMIT ?", (limit,)
    )).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────── BOOKING CONFLICT HELPERS ───────────────────────────

_BOOKING_TIME_RE = _re.compile(r"(\d{1,2}):(\d{2})\s*[-–—]\s*(\d{1,2}):(\d{2})")


async def get_booking_blocks_for_date_zone(date_str: str, zone: str) -> list[tuple[int, int]]:
    """Return list of (start_min, end_min) for active bookings on date_str (YYYY-MM-DD) and zone.
    Bookings with status 'cancelled' are excluded.
    """
    db = await get_db()
    rows = await (await db.execute(
        """SELECT booking_time FROM bookings
           WHERE booking_date = ? AND zone = ? AND status != 'cancelled'""",
        (date_str, zone),
    )).fetchall()
    result: list[tuple[int, int]] = []
    for row in rows:
        m = _BOOKING_TIME_RE.search(row[0])
        if m:
            s_min = int(m.group(1)) * 60 + int(m.group(2))
            e_min = int(m.group(3)) * 60 + int(m.group(4))
            result.append((s_min, e_min))
    return result


async def get_zone_date_statuses_for_month(
    zone: str, year: int, month: int
) -> dict[str, str]:
    """Return {date_iso: 'partial'|'full'} for the given zone + month.
    Combines zone booking blocks with birthday blocks (birthdays affect ALL zones).
    'full'    = no 30-minute slot is free.
    'partial' = some bookings exist but at least one 30-min slot remains.
    Dates absent from the result are fully free.
    """
    from config import BIRTHDAY_CLEANUP_MINUTES

    month_prefix = f"{year:04d}-{month:02d}-"
    db = await get_db()

    # ── Zone booking blocks (ISO date format only) ──
    rows = await (await db.execute(
        """SELECT booking_date, booking_time FROM bookings
           WHERE booking_date LIKE ? AND zone = ? AND status != 'cancelled'""",
        (month_prefix + "%", zone),
    )).fetchall()

    zone_blocks: dict[str, list[tuple[int, int]]] = {}
    zone_has_bookings: set[str] = set()   # dates with any booking (even no time range)
    for row in rows:
        date_str, time_str = row[0], row[1]
        zone_has_bookings.add(date_str)
        m = _BOOKING_TIME_RE.search(time_str)
        if m:
            s_min = int(m.group(1)) * 60 + int(m.group(2))
            e_min = int(m.group(3)) * 60 + int(m.group(4))
            zone_blocks.setdefault(date_str, []).append((s_min, e_min))

    # ── Birthday blocks (affect all zones) ──
    bday_rows = await (await db.execute(
        """SELECT birthday_date, birthday_time_start, birthday_time_end
           FROM birthday_orders
           WHERE birthday_date LIKE ? AND status NOT IN ('rejected', 'cancelled')
             AND birthday_time_start IS NOT NULL AND birthday_time_end IS NOT NULL
             AND birthday_time_start != '' AND birthday_time_end != ''""",
        (month_prefix + "%",),
    )).fetchall()

    bday_blocks: dict[str, list[tuple[int, int]]] = {}
    for row in bday_rows:
        date_str, ts, te = row[0], row[1], row[2]
        try:
            sh, sm = map(int, ts.split(":"))
            eh, em = map(int, te.split(":"))
            bday_blocks.setdefault(date_str, []).append(
                (sh * 60 + sm, eh * 60 + em + BIRTHDAY_CLEANUP_MINUTES)
            )
        except Exception:
            pass

    all_dates = set(zone_blocks.keys()) | set(bday_blocks.keys()) | zone_has_bookings
    result: dict[str, str] = {}

    _OPEN  = 13 * 60   # 13:00
    _CLOSE = 23 * 60   # 23:00
    _STEP  = 30

    for date_str in all_dates:
        combined = zone_blocks.get(date_str, []) + bday_blocks.get(date_str, [])
        if not combined:
            # No time-range blocks but date has regular bookings → partial
            if date_str in zone_has_bookings:
                result[date_str] = "partial"
            continue

        # Scan every 30-min window to see if any is free
        has_free = False
        t = _OPEN
        while t + _STEP <= _CLOSE:
            if not any(t < b_e and b_s < t + _STEP for b_s, b_e in combined):
                has_free = True
                break
            t += _STEP

        result[date_str] = "partial" if has_free else "full"

    return result


# ─────────────────────────── SUGGESTIONS ───────────────────────────

async def create_suggestion(user_tg_id: int, text: str) -> int:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO suggestions (user_tg_id, text) VALUES (?, ?)",
        (user_tg_id, text),
    )
    await db.commit()
    return cur.lastrowid


# ─────────────────────────── PS GAMES ───────────────────────────

async def get_games(platform: str) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM ps_games WHERE platform=? ORDER BY sort_order, title",
        (platform,)
    )).fetchall()
    return [dict(r) for r in rows]


async def add_game(platform: str, title: str, image_file_id: str = "") -> int:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO ps_games (platform, title, image_file_id) VALUES (?, ?, ?)",
        (platform, title, image_file_id),
    )
    await db.commit()
    return cur.lastrowid


async def delete_game(game_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM ps_games WHERE id=?", (game_id,))
    await db.commit()


# ─────────────────────────── INSTRUCTIONS ───────────────────────────

async def get_all_instructions() -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM board_game_instructions ORDER BY sort_order, game_name"
    )).fetchall()
    return [dict(r) for r in rows]


async def get_instruction(instruction_id: int) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM board_game_instructions WHERE id=?", (instruction_id,)
    )).fetchone()
    return dict(row) if row else None


async def add_instruction(
    game_name: str,
    content_type: str = "text",
    text_content: str = "",
    file_id: str = "",
) -> int:
    db = await get_db()
    cur = await db.execute(
        """INSERT INTO board_game_instructions
           (game_name, content_type, text_content, file_id)
           VALUES (?, ?, ?, ?)""",
        (game_name, content_type, text_content, file_id),
    )
    await db.commit()
    return cur.lastrowid


async def delete_instruction(instruction_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM board_game_instructions WHERE id=?", (instruction_id,))
    await db.commit()


# ─────────────────────────── GALLERY ───────────────────────────

async def get_gallery() -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM gallery ORDER BY sort_order, id"
    )).fetchall()
    return [dict(r) for r in rows]


async def add_gallery_photo(file_id: str, caption: str = "", category: str = "general") -> int:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO gallery (file_id, caption, category) VALUES (?, ?, ?)",
        (file_id, caption, category),
    )
    await db.commit()
    return cur.lastrowid


async def delete_gallery_photo(photo_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM gallery WHERE id=?", (photo_id,))
    await db.commit()


# ─────────────────────────── BOOKING DETAIL / STATUS ───────────────────────────

async def get_booking(booking_id: int) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM bookings WHERE id=?", (booking_id,)
    )).fetchone()
    return dict(row) if row else None


async def update_booking_status(booking_id: int, status: str) -> None:
    db = await get_db()
    await db.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
    await db.commit()


# ─────────────────────────── BIRTHDAY ORDER DETAIL / STATUS ───────────────────────────

async def get_birthday_order(order_id: int) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM birthday_orders WHERE id=?", (order_id,)
    )).fetchone()
    return dict(row) if row else None


async def update_birthday_status(order_id: int, status: str) -> None:
    db = await get_db()
    await db.execute("UPDATE birthday_orders SET status=? WHERE id=?", (status, order_id))
    await db.commit()


async def delete_booking(booking_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    await db.commit()


async def delete_birthday_order(order_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM birthday_orders WHERE id=?", (order_id,))
    await db.commit()


# ─────────────────────────── STATISTICS ───────────────────────────

async def get_stats() -> dict:
    db = await get_db()

    def _n(row) -> int:
        return row[0] if row else 0

    async def q(sql: str, *args) -> int:
        return _n(await (await db.execute(sql, args)).fetchone())

    total_users     = await q("SELECT COUNT(*) FROM users")
    blocked_users   = await q("SELECT COUNT(*) FROM users WHERE is_blocked=1")
    new_week_users  = await q("SELECT COUNT(*) FROM users WHERE created_at >= datetime('now','-7 days')")

    total_bookings     = await q("SELECT COUNT(*) FROM bookings")
    pending_bookings   = await q("SELECT COUNT(*) FROM bookings WHERE status='pending'")
    confirmed_bookings = await q("SELECT COUNT(*) FROM bookings WHERE status='confirmed'")
    cancelled_bookings = await q("SELECT COUNT(*) FROM bookings WHERE status='cancelled'")
    week_bookings      = await q("SELECT COUNT(*) FROM bookings WHERE created_at >= datetime('now','-7 days')")
    month_bookings     = await q("SELECT COUNT(*) FROM bookings WHERE created_at >= datetime('now','-30 days')")

    zone_rows = await (await db.execute(
        "SELECT zone, COUNT(*) AS cnt FROM bookings GROUP BY zone ORDER BY cnt DESC"
    )).fetchall()
    zones = [(r[0], r[1]) for r in zone_rows]

    total_birthdays     = await q("SELECT COUNT(*) FROM birthday_orders")
    pending_birthdays   = await q("SELECT COUNT(*) FROM birthday_orders WHERE status='pending'")
    confirmed_birthdays = await q("SELECT COUNT(*) FROM birthday_orders WHERE status='confirmed'")
    cancelled_birthdays = await q("SELECT COUNT(*) FROM birthday_orders WHERE status='cancelled'")
    week_birthdays      = await q("SELECT COUNT(*) FROM birthday_orders WHERE created_at >= datetime('now','-7 days')")
    month_birthdays     = await q("SELECT COUNT(*) FROM birthday_orders WHERE created_at >= datetime('now','-30 days')")

    total_suggestions = await q("SELECT COUNT(*) FROM suggestions")

    return {
        "total_users":        total_users,
        "blocked_users":      blocked_users,
        "new_week_users":     new_week_users,
        "total_bookings":     total_bookings,
        "pending_bookings":   pending_bookings,
        "confirmed_bookings": confirmed_bookings,
        "cancelled_bookings": cancelled_bookings,
        "week_bookings":      week_bookings,
        "month_bookings":     month_bookings,
        "zones":              zones,
        "total_birthdays":     total_birthdays,
        "pending_birthdays":   pending_birthdays,
        "confirmed_birthdays": confirmed_birthdays,
        "cancelled_birthdays": cancelled_birthdays,
        "week_birthdays":      week_birthdays,
        "month_birthdays":     month_birthdays,
        "total_suggestions":  total_suggestions,
    }


# ─────────────────────────── USER BLOCKING ───────────────────────────

async def block_user(tg_id: int) -> None:
    db = await get_db()
    await db.execute("UPDATE users SET is_blocked=1 WHERE tg_id=?", (tg_id,))
    await db.commit()


async def unblock_user(tg_id: int) -> None:
    db = await get_db()
    await db.execute("UPDATE users SET is_blocked=0 WHERE tg_id=?", (tg_id,))
    await db.commit()


async def is_user_blocked(tg_id: int) -> bool:
    db = await get_db()
    row = await (await db.execute(
        "SELECT is_blocked FROM users WHERE tg_id=?", (tg_id,)
    )).fetchone()
    return bool(row[0]) if row and row[0] else False


async def get_all_users(limit: int = 500) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,)
    )).fetchall()
    return [dict(r) for r in rows]


async def get_all_users_for_broadcast() -> list[int]:
    """Return tg_ids of all non-blocked users."""
    db = await get_db()
    rows = await (await db.execute(
        "SELECT tg_id FROM users WHERE is_blocked=0 OR is_blocked IS NULL"
    )).fetchall()
    return [r[0] for r in rows]


async def count_user_bookings(tg_id: int) -> int:
    db = await get_db()
    row = await (await db.execute(
        "SELECT COUNT(*) FROM bookings WHERE user_tg_id=?", (tg_id,)
    )).fetchone()
    return row[0] if row else 0


# ─────────────────────────── PROFILE ───────────────────────────

async def save_user_profile(
    tg_id: int,
    name: str | None = None,
    phone: str | None = None,
) -> None:
    db = await get_db()
    if name is not None:
        await db.execute("UPDATE users SET saved_name=? WHERE tg_id=?", (name, tg_id))
    if phone is not None:
        await db.execute("UPDATE users SET saved_phone=? WHERE tg_id=?", (phone, tg_id))
    await db.commit()


# ─────────────────────────── POINTS ───────────────────────────

async def add_points_with_history(
    tg_id: int,
    amount: int,
    type_: str,
    description: str,
    ref_id: int | None = None,
) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE users SET points = points + ? WHERE tg_id = ?", (amount, tg_id)
    )
    await db.execute(
        "INSERT INTO points_history (tg_id, type, amount, description, ref_id) VALUES (?, ?, ?, ?, ?)",
        (tg_id, type_, amount, description, ref_id),
    )
    await db.commit()


async def get_points_history(
    tg_id: int, page: int = 0, per_page: int = 8
) -> tuple[list[dict], int]:
    db = await get_db()
    total_row = await (await db.execute(
        "SELECT COUNT(*) FROM points_history WHERE tg_id=?", (tg_id,)
    )).fetchone()
    total = total_row[0] if total_row else 0
    offset = page * per_page
    rows = await (await db.execute(
        "SELECT * FROM points_history WHERE tg_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (tg_id, per_page, offset),
    )).fetchall()
    return [dict(r) for r in rows], total


# ─────────────────────────── WALLET ───────────────────────────

async def create_wallet_topup(tg_id: int, amount: int, comment: str = "") -> int:
    from config import WALLET_BONUS_PCT
    bonus = int(amount * WALLET_BONUS_PCT / 100)
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO wallet_transactions (tg_id, type, amount, bonus, status, comment) VALUES (?, 'topup', ?, ?, 'pending', ?)",
        (tg_id, amount, bonus, comment),
    )
    await db.commit()
    return cur.lastrowid


async def confirm_wallet_topup(tx_id: int) -> dict | None:
    db = await get_db()
    tx_row = await (await db.execute(
        "SELECT * FROM wallet_transactions WHERE id=? AND status='pending'", (tx_id,)
    )).fetchone()
    if not tx_row:
        return None
    tx = dict(tx_row)
    total = tx["amount"] + tx["bonus"]
    await db.execute("UPDATE wallet_transactions SET status='confirmed' WHERE id=?", (tx_id,))
    await db.execute(
        "UPDATE users SET wallet_balance = wallet_balance + ? WHERE tg_id=?",
        (total, tx["tg_id"]),
    )
    await db.commit()
    return tx


async def cancel_wallet_topup(tx_id: int) -> dict | None:
    db = await get_db()
    tx_row = await (await db.execute(
        "SELECT * FROM wallet_transactions WHERE id=? AND status='pending'", (tx_id,)
    )).fetchone()
    if not tx_row:
        return None
    tx = dict(tx_row)
    await db.execute("UPDATE wallet_transactions SET status='cancelled' WHERE id=?", (tx_id,))
    await db.commit()
    return tx


async def get_pending_topups() -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        """SELECT wt.*, u.full_name, u.username
           FROM wallet_transactions wt
           LEFT JOIN users u ON wt.tg_id = u.tg_id
           WHERE wt.status='pending'
           ORDER BY wt.created_at ASC"""
    )).fetchall()
    return [dict(r) for r in rows]


async def get_wallet_history(tg_id: int) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM wallet_transactions WHERE tg_id=? ORDER BY created_at DESC LIMIT 20",
        (tg_id,),
    )).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────── REFERRALS ───────────────────────────

async def get_referrals(tg_id: int) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT tg_id, full_name, username, created_at FROM users WHERE referred_by=? ORDER BY created_at DESC",
        (tg_id,),
    )).fetchall()
    return [dict(r) for r in rows]


async def apply_referral_code(tg_id: int, code: str) -> str:
    """Apply a referral code for a user.
    Returns: 'ok' | 'already_set' | 'not_found' | 'own_code'
    """
    db = await get_db()
    user_row = await (await db.execute(
        "SELECT referred_by FROM users WHERE tg_id=?", (tg_id,)
    )).fetchone()
    if not user_row:
        return "not_found"
    if user_row[0]:
        return "already_set"
    ref_row = await (await db.execute(
        "SELECT tg_id FROM users WHERE referral_code=?", (code.strip().upper(),)
    )).fetchone()
    if not ref_row:
        return "not_found"
    referrer_id = ref_row[0]
    if referrer_id == tg_id:
        return "own_code"
    await db.execute("UPDATE users SET referred_by=? WHERE tg_id=?", (referrer_id, tg_id))
    await db.commit()
    return "ok"


async def calc_and_award_referral_bonuses(year: int, month: int) -> dict:
    """Calculate 3% of referrals' monthly spending and award to referrers.
    Uses price stored in bookings/birthday_orders for the given month.
    Returns: {referrers_count, total_points}.
    """
    from config import REFERRAL_PCT
    db = await get_db()
    month_prefix = f"{year:04d}-{month:02d}-%"

    booking_rows = await (await db.execute(
        """SELECT u.referred_by, COALESCE(SUM(b.price), 0) AS total
           FROM users u
           JOIN bookings b ON u.tg_id = b.user_tg_id
           WHERE b.booking_date LIKE ? AND b.status != 'cancelled'
             AND u.referred_by IS NOT NULL AND u.referred_by > 0
           GROUP BY u.referred_by""",
        (month_prefix,),
    )).fetchall()

    birthday_rows = await (await db.execute(
        """SELECT u.referred_by, COALESCE(SUM(bo.price), 0) AS total
           FROM users u
           JOIN birthday_orders bo ON u.tg_id = bo.user_tg_id
           WHERE bo.birthday_date LIKE ? AND bo.status != 'rejected'
             AND u.referred_by IS NOT NULL AND u.referred_by > 0
           GROUP BY u.referred_by""",
        (month_prefix,),
    )).fetchall()

    totals: dict[int, int] = {}
    for row in booking_rows:
        totals[row[0]] = totals.get(row[0], 0) + row[1]
    for row in birthday_rows:
        totals[row[0]] = totals.get(row[0], 0) + row[1]

    month_label = f"{year:04d}-{month:02d}"
    total_awarded = 0
    count = 0
    for referrer_id, spending in totals.items():
        points = int(spending * REFERRAL_PCT / 100)
        if points > 0:
            await add_points_with_history(
                referrer_id, points, "referral",
                f"Реферальні бали за {month_label}",
            )
            total_awarded += points
            count += 1

    return {"referrers_count": count, "total_points": total_awarded}


# ─────────────────────────── BUNKER GAME ───────────────────────────

import json as _json
import random as _random
import string as _string

_BUNKER_ATTR_TYPES = ["profession", "health", "hobby", "phobia", "baggage", "ability"]


def _gen_session_code() -> str:
    return "".join(_random.choices(_string.ascii_uppercase + _string.digits, k=6))


async def create_bunker_session(host_tg_id: int, max_players: int) -> dict:
    db = await get_db()
    for _ in range(10):
        code = _gen_session_code()
        try:
            cur = await db.execute(
                """INSERT INTO bunker_sessions (code, host_tg_id, max_players)
                   VALUES (?, ?, ?)""",
                (code, host_tg_id, max_players),
            )
            await db.commit()
            row = await (await db.execute(
                "SELECT * FROM bunker_sessions WHERE id=?", (cur.lastrowid,)
            )).fetchone()
            return dict(row)
        except Exception:
            continue
    raise RuntimeError("Failed to generate unique bunker session code")


async def get_bunker_session(session_id: int) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM bunker_sessions WHERE id=?", (session_id,)
    )).fetchone()
    return dict(row) if row else None


async def get_bunker_session_by_code(code: str) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM bunker_sessions WHERE code=? AND status != 'ended'",
        (code.strip().upper(),),
    )).fetchone()
    return dict(row) if row else None


async def update_bunker_session(session_id: int, **kwargs) -> None:
    db = await get_db()
    if not kwargs:
        return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [session_id]
    await db.execute(f"UPDATE bunker_sessions SET {sets} WHERE id=?", vals)
    await db.commit()


async def delete_bunker_session(session_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM bunker_votes WHERE session_id=?", (session_id,))
    await db.execute("DELETE FROM bunker_players WHERE session_id=?", (session_id,))
    await db.execute("DELETE FROM bunker_sessions WHERE id=?", (session_id,))
    await db.commit()


async def add_bunker_player(session_id: int, tg_id: int, display_name: str) -> bool:
    """Returns False if already in session."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO bunker_players (session_id, tg_id, display_name) VALUES (?, ?, ?)",
            (session_id, tg_id, display_name),
        )
        await db.commit()
        return True
    except Exception:
        return False


async def get_bunker_players(session_id: int) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM bunker_players WHERE session_id=? ORDER BY joined_at",
        (session_id,),
    )).fetchall()
    return [dict(r) for r in rows]


async def get_alive_bunker_players(session_id: int) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM bunker_players WHERE session_id=? AND is_alive=1 ORDER BY joined_at",
        (session_id,),
    )).fetchall()
    return [dict(r) for r in rows]


async def get_bunker_player(session_id: int, tg_id: int) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM bunker_players WHERE session_id=? AND tg_id=?",
        (session_id, tg_id),
    )).fetchone()
    return dict(row) if row else None


async def update_bunker_player(session_id: int, tg_id: int, **kwargs) -> None:
    db = await get_db()
    if not kwargs:
        return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [session_id, tg_id]
    await db.execute(
        f"UPDATE bunker_players SET {sets} WHERE session_id=? AND tg_id=?", vals
    )
    await db.commit()


async def start_bunker_game(session_id: int) -> dict:
    """Assign cards to all players, pick scenario. Returns updated session dict."""
    db = await get_db()

    # Pick random catastrophe and bunker scenario
    cat_row = await (await db.execute(
        "SELECT * FROM bunker_scenarios WHERE type='catastrophe' ORDER BY RANDOM() LIMIT 1"
    )).fetchone()
    bun_row = await (await db.execute(
        "SELECT * FROM bunker_scenarios WHERE type='bunker' ORDER BY RANDOM() LIMIT 1"
    )).fetchone()

    session = await get_bunker_session(session_id)
    n_players = session["max_players"]

    # Capacity from bunker scenario, capped sensibly
    capacity = 3
    if bun_row:
        cap_min = bun_row["capacity_min"]
        cap_max = min(bun_row["capacity_max"], n_players - 1)
        capacity = max(2, _random.randint(cap_min, max(cap_min, cap_max)))
        capacity = min(capacity, n_players - 1)

    cat_text = cat_row["text_uk"] if cat_row else "Невідома катастрофа"
    bun_text = bun_row["text_uk"] if bun_row else "Підземний бункер"

    # Assign attributes — no duplicates within session
    pools: dict[str, list] = {}
    for attr_type in _BUNKER_ATTR_TYPES:
        rows = await (await db.execute(
            "SELECT text_uk FROM bunker_attributes WHERE type=? ORDER BY RANDOM()",
            (attr_type,),
        )).fetchall()
        pool = [r[0] for r in rows]
        _random.shuffle(pool)
        pools[attr_type] = pool

    players = await get_bunker_players(session_id)
    n_players = len(players)
    # Ensure each pool has enough items (extend by repeating if seed content is sparse)
    for attr_type in _BUNKER_ATTR_TYPES:
        pool = pools[attr_type]
        if pool and len(pool) < n_players:
            pool = (pool * (n_players // len(pool) + 1))[:n_players]
            _random.shuffle(pool)
            pools[attr_type] = pool

    for i, player in enumerate(players):
        card = {}
        for attr_type in _BUNKER_ATTR_TYPES:
            pool = pools[attr_type]
            card[attr_type] = pool[i] if pool else "—"
        await db.execute(
            "UPDATE bunker_players SET card_json=?, revealed='[]' WHERE session_id=? AND tg_id=?",
            (_json.dumps(card, ensure_ascii=False), session_id, player["tg_id"]),
        )

    await db.execute(
        """UPDATE bunker_sessions
           SET status='active', catastrophe_text=?, bunker_text=?, bunker_capacity=?
           WHERE id=?""",
        (cat_text, bun_text, capacity, session_id),
    )
    await db.commit()
    return await get_bunker_session(session_id)


async def mark_attr_revealed(session_id: int, tg_id: int, attr: str) -> None:
    player = await get_bunker_player(session_id, tg_id)
    if not player:
        return
    revealed = _json.loads(player["revealed"] or "[]")
    if attr not in revealed:
        revealed.append(attr)
    await update_bunker_player(
        session_id, tg_id, revealed=_json.dumps(revealed, ensure_ascii=False)
    )


async def record_bunker_vote(
    session_id: int, vote_round: int, voter_tg_id: int, target_tg_id: int
) -> bool:
    """Returns False if already voted this round."""
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO bunker_votes (session_id, vote_round, voter_tg_id, target_tg_id)
               VALUES (?, ?, ?, ?)""",
            (session_id, vote_round, voter_tg_id, target_tg_id),
        )
        await db.commit()
        return True
    except Exception:
        return False


async def get_bunker_vote_results(session_id: int, vote_round: int) -> dict:
    """Returns {target_tg_id: [voter_tg_id, ...]} for the given round."""
    db = await get_db()
    rows = await (await db.execute(
        "SELECT voter_tg_id, target_tg_id FROM bunker_votes WHERE session_id=? AND vote_round=?",
        (session_id, vote_round),
    )).fetchall()
    results: dict[int, list[int]] = {}
    for row in rows:
        results.setdefault(row[1], []).append(row[0])
    return results


async def get_pending_vote_players(session_id: int, vote_round: int) -> list[int]:
    """Returns tg_ids of alive players who haven't voted yet this round."""
    db = await get_db()
    voted_rows = await (await db.execute(
        "SELECT voter_tg_id FROM bunker_votes WHERE session_id=? AND vote_round=?",
        (session_id, vote_round),
    )).fetchall()
    voted = {r[0] for r in voted_rows}
    alive = await get_alive_bunker_players(session_id)
    return [p["tg_id"] for p in alive if p["tg_id"] not in voted]


async def eliminate_bunker_player(session_id: int, tg_id: int) -> None:
    await update_bunker_player(session_id, tg_id, is_alive=0)


# ─── Bunker Events (Phase 5) ─────────────────────────────────────────────────

async def create_bunker_event(
    session_id: int,
    event_code: str,
    dc: int,
    executor_tg_id: int = 0,
    modifier: int = 0,
    is_auto: int = 0,
    victim_tg_id: int = 0,
    thief_tg_id: int = 0,
    round_num: int = 0,
) -> dict:
    """Create a new active event record. Returns the created event dict."""
    db = await get_db()
    cur = await db.execute(
        """INSERT INTO bunker_active_events
           (session_id, event_code, dc, executor_tg_id, modifier, is_auto,
            victim_tg_id, thief_tg_id, round_num)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, event_code, dc, executor_tg_id, modifier, is_auto,
         victim_tg_id, thief_tg_id, round_num),
    )
    await db.commit()
    row = await (await db.execute(
        "SELECT * FROM bunker_active_events WHERE id=?", (cur.lastrowid,)
    )).fetchone()
    return dict(row)


async def get_active_bunker_event(session_id: int) -> dict | None:
    """Return the latest unresolved event for the session."""
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM bunker_active_events WHERE session_id=? AND is_resolved=0 ORDER BY id DESC LIMIT 1",
        (session_id,),
    )).fetchone()
    return dict(row) if row else None


async def get_bunker_event(event_id: int) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM bunker_active_events WHERE id=?", (event_id,)
    )).fetchone()
    return dict(row) if row else None


async def update_bunker_event(event_id: int, **kwargs) -> None:
    db = await get_db()
    if not kwargs:
        return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [event_id]
    await db.execute(f"UPDATE bunker_active_events SET {sets} WHERE id=?", vals)
    await db.commit()


async def resolve_bunker_event(
    event_id: int,
    roll_result: int = 0,
    outcome: str = "",
) -> None:
    await update_bunker_event(event_id, roll_result=roll_result, outcome=outcome, is_resolved=1)


async def get_recent_event_codes(session_id: int, limit: int = 2) -> list[str]:
    """Return codes of the last N resolved events (for cooldown logic)."""
    db = await get_db()
    rows = await (await db.execute(
        "SELECT event_code FROM bunker_active_events WHERE session_id=? AND is_resolved=1 ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )).fetchall()
    return [r[0] for r in rows]


# ─── Player statuses ──────────────────────────────────────────────────────────

async def set_player_status(
    session_id: int, tg_id: int, status: str, expires_round: int = 0
) -> None:
    db = await get_db()
    await db.execute(
        """INSERT INTO bunker_player_statuses (session_id, tg_id, status, expires_round)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(session_id, tg_id) DO UPDATE SET status=excluded.status, expires_round=excluded.expires_round""",
        (session_id, tg_id, status, expires_round),
    )
    await db.commit()


async def clear_player_status(session_id: int, tg_id: int) -> None:
    db = await get_db()
    await db.execute(
        "DELETE FROM bunker_player_statuses WHERE session_id=? AND tg_id=?",
        (session_id, tg_id),
    )
    await db.commit()


async def get_player_status(session_id: int, tg_id: int) -> str | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT status FROM bunker_player_statuses WHERE session_id=? AND tg_id=?",
        (session_id, tg_id),
    )).fetchone()
    return row[0] if row else None


async def get_all_player_statuses(session_id: int) -> dict[int, str]:
    """Return {tg_id: status} for all players with active statuses."""
    db = await get_db()
    rows = await (await db.execute(
        "SELECT tg_id, status FROM bunker_player_statuses WHERE session_id=?",
        (session_id,),
    )).fetchall()
    return {r[0]: r[1] for r in rows}

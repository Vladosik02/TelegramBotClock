"""
Bunker game handler.

Roles:
  Host  — creates session, manages reveal rounds and voting, sees all cards.
  Player — joins by code, receives private card, reveals attributes, votes.

Session state is stored in DB (spans multiple users).
FSM is used only for short text-input flows (code entry).
"""
import json
import logging
import random

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.db import (
    create_bunker_session,
    get_bunker_session,
    get_bunker_session_by_code,
    update_bunker_session,
    delete_bunker_session,
    add_bunker_player,
    get_bunker_players,
    get_alive_bunker_players,
    get_bunker_player,
    update_bunker_player,
    start_bunker_game,
    mark_attr_revealed,
    record_bunker_vote,
    get_bunker_vote_results,
    get_pending_vote_players,
    eliminate_bunker_player,
    get_user_lang,
    # Phase 5 — events
    create_bunker_event,
    get_active_bunker_event,
    get_bunker_event,
    update_bunker_event,
    resolve_bunker_event,
    get_recent_event_codes,
    get_bunker_event_history,
    set_player_status,
    clear_player_status,
    get_player_status,
    get_all_player_statuses,
)
from keyboards.kb import (
    bunker_menu_keyboard,
    bunker_player_count_keyboard,
    bunker_host_waiting_keyboard,
    bunker_host_game_keyboard,
    bunker_player_card_keyboard,
    bunker_player_confirm_keyboard,
    bunker_vote_keyboard,
    bunker_host_kick_keyboard,
    back_to_menu_keyboard,
    # Phase 5 — events
    bunker_event_roll_keyboard,
    bunker_steal_victim_keyboard,
    bunker_steal_attr_keyboard,
)
from locales import t
from states.forms import BunkerHostForm, BunkerPlayerForm
from utils.bunker_events import (
    pick_event,
    find_executor,
    find_detective,
    roll_d20,
    resolve_roll,
    get_consequence,
    event_name,
    event_text,
    EVENT_DEFINITIONS,
)

router = Router()

_ATTR_KEYS = ["age", "profession", "health", "hobby", "phobia", "baggage", "ability"]


# ─────────────────────── helpers ────────────────────────────────────────────

async def _get_lang(tg_id: int) -> str:
    return await get_user_lang(tg_id)


async def _push(bot: Bot, tg_id: int, text: str, **kwargs) -> None:
    """Send a message to a user, silently ignoring Telegram errors."""
    try:
        await bot.send_message(tg_id, text, parse_mode="HTML", **kwargs)
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logging.warning("bunker push to %s failed: %s", tg_id, e)


def _status_bar(alive_count: int, capacity: int, round_num: int = 0) -> str:
    s = f"🟢 Живих: {alive_count} | 🏠 Місця: {capacity}"
    if round_num:
        s += f" | ⚔️ Раунд: {round_num}"
    return s


def _card_text(card: dict, lang: str) -> str:
    lines = []
    for attr in _ATTR_KEYS:
        attr_name = t(f"bunker_attr_{attr}", lang)
        value = card.get(attr, "—")
        lines.append(t("bunker_card_line", lang, attr=attr_name, value=value))
    return "\n".join(lines)


def _cards_summary(players: list[dict], lang: str) -> str:
    """Host view: name + all attributes for each player."""
    lines = []
    for p in players:
        card = json.loads(p["card_json"] or "{}")
        revealed = json.loads(p["revealed"] or "[]")
        name = p["display_name"]
        lines.append(f"\n👤 <b>{name}</b>")
        for attr in _ATTR_KEYS:
            attr_name = t(f"bunker_attr_{attr}", lang)
            value = card.get(attr, "—")
            mark = "✅" if attr in revealed else "🔒"
            lines.append(f"  {mark} {attr_name}: {value}")
    return "\n".join(lines)


_ATTR_EMOJI = {
    "age": "🎂",
    "profession": "💼", "health": "❤️", "hobby": "🎯",
    "phobia": "😨", "baggage": "🎒", "ability": "⚡",
}
_STATUS_EMOJI_MAP = {
    "sick": "🤒", "immune": "💊", "breakdown": "😤",
    "thief": "🎭", "detective": "🔍", "repairing": "🛠️",
    "blackout": "⚡", "skip_turn": "🚫",
}


def _cards_compact(
    alive: list[dict],
    eliminated: list[dict],
    statuses: dict[int, str],
    lang: str,
) -> str:
    """Compact host cards view — only revealed attrs + status emoji."""
    lines = []
    total_attrs = len(_ATTR_KEYS)
    for p in alive:
        card = json.loads(p["card_json"] or "{}")
        revealed = json.loads(p["revealed"] or "[]")
        st = _STATUS_EMOJI_MAP.get(statuses.get(p["tg_id"], ""), "")
        st_str = f" {st}" if st else ""
        rev_count = len(revealed)
        lines.append(f"👤 <b>{p['display_name']}</b> ({rev_count}/{total_attrs}){st_str}")
        if revealed:
            parts = [
                f"{_ATTR_EMOJI.get(a, '')} {card.get(a, '—')}"
                for a in _ATTR_KEYS if a in revealed
            ]
            lines.append("  " + "  •  ".join(parts))
        else:
            lines.append(f"  <i>{t('bunker_cards_nothing_revealed', lang)}</i>")
        lines.append("")
    # trim trailing blank line
    while lines and lines[-1] == "":
        lines.pop()
    if eliminated:
        lines.append("──────────────")
        elim = "  •  ".join(f"<b>{p['display_name']}</b>" for p in eliminated)
        lines.append(f"💀 {elim}")
    return "\n".join(lines)


def _round_status_text(alive: list[dict], reveal_round: int, lang: str) -> str:
    """Build status list: who has revealed in this round (len(revealed) >= reveal_round)."""
    lines = []
    for p in alive:
        revealed = json.loads(p["revealed"] or "[]")
        if len(revealed) >= reveal_round:
            lines.append(t("bunker_reveal_status_done", lang, name=p["display_name"]))
        else:
            lines.append(t("bunker_reveal_status_waiting", lang, name=p["display_name"]))
    return "\n".join(lines)


async def _find_host_session(tg_id: int):
    """Find an active (waiting or active) session where tg_id is host."""
    from database.db import get_db
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM bunker_sessions WHERE host_tg_id=? AND status IN ('waiting','active') ORDER BY id DESC LIMIT 1",
        (tg_id,),
    )).fetchone()
    return dict(row) if row else None


async def _find_player_session(tg_id: int):
    """Find an active session where tg_id is a player."""
    from database.db import get_db
    db = await get_db()
    row = await (await db.execute(
        """SELECT s.* FROM bunker_sessions s
           JOIN bunker_players p ON s.id = p.session_id
           WHERE p.tg_id=? AND s.status IN ('waiting','active')
           ORDER BY s.id DESC LIMIT 1""",
        (tg_id,),
    )).fetchone()
    return dict(row) if row else None


# ─────────────────────── entry point ────────────────────────────────────────

@router.callback_query(F.data == "menu:bunker")
async def cb_bunker_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await _get_lang(callback.from_user.id)
    await callback.message.edit_text(
        t("bunker_menu_title", lang),
        reply_markup=bunker_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────── RULES ──────────────────────────────────────────────

@router.callback_query(F.data == "bunker:rules")
async def cb_bunker_rules(callback: CallbackQuery) -> None:
    lang = await _get_lang(callback.from_user.id)
    await callback.message.answer(
        t("bunker_rules", lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────── HOST: create session ────────────────────────────────

@router.callback_query(F.data == "bunker:create")
async def cb_bunker_create(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await _get_lang(callback.from_user.id)
    existing = await _find_host_session(callback.from_user.id)
    if existing:
        await callback.answer(t("bunker_already_host", lang), show_alert=True)
        return
    await state.set_state(BunkerHostForm.selecting_count)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("bunker_select_count", lang),
        reply_markup=bunker_player_count_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^bunker:host_count:\d+$"), BunkerHostForm.selecting_count)
async def cb_bunker_host_count(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    await state.clear()

    max_players = int(callback.data.split(":")[-1])
    if not (4 <= max_players <= 12):
        await callback.answer("⛔", show_alert=True)
        return
    session = await create_bunker_session(callback.from_user.id, max_players)

    await callback.message.edit_text(
        t("bunker_session_created", lang,
          code=session["code"], joined=0, max=max_players),
        reply_markup=bunker_host_waiting_keyboard(session["id"], 0, max_players, lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────── HOST: cancel session ────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:cancel:\d+$"))
async def cb_bunker_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)
    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return

    players = await get_bunker_players(session_id)
    await delete_bunker_session(session_id)

    for p in players:
        await _push(callback.bot, p["tg_id"],
                    t("bunker_session_cancelled", await _get_lang(p["tg_id"])))

    await state.clear()
    await callback.message.edit_text(
        t("bunker_session_cancelled", lang),
        reply_markup=bunker_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────── PLAYER: join session ────────────────────────────────

@router.callback_query(F.data == "bunker:join")
async def cb_bunker_join(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await _get_lang(callback.from_user.id)
    await state.set_state(BunkerPlayerForm.entering_code)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("bunker_enter_code", lang),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(BunkerPlayerForm.entering_code)
async def msg_bunker_code(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    code = (message.text or "").strip().upper()

    session = await get_bunker_session_by_code(code)
    if not session:
        await message.answer(t("bunker_code_not_found", lang), parse_mode="HTML")
        return

    session_id = session["id"]
    players = await get_bunker_players(session_id)

    if any(p["tg_id"] == message.from_user.id for p in players):
        await message.answer(t("bunker_already_joined", lang), parse_mode="HTML")
        await state.clear()
        return

    if len(players) >= session["max_players"]:
        await message.answer(t("bunker_session_full", lang), parse_mode="HTML")
        return

    display_name = message.from_user.full_name or message.from_user.username or f"Гравець {len(players)+1}"
    await add_bunker_player(session_id, message.from_user.id, display_name)
    await state.clear()

    await message.answer(
        t("bunker_joined", lang, code=session["code"]),
        parse_mode="HTML",
    )

    # Notify host about new player
    players_updated = await get_bunker_players(session_id)
    joined = len(players_updated)
    host_lang = await _get_lang(session["host_tg_id"])
    player_list = "\n".join(f"  • {p['display_name']}" for p in players_updated)
    await _push(
        bot,
        session["host_tg_id"],
        t("bunker_waiting_update", host_lang,
          code=session["code"], joined=joined, max=session["max_players"],
          player_list=player_list),
        reply_markup=bunker_host_waiting_keyboard(session_id, joined, session["max_players"], host_lang),
    )


# ─────────────────────── HOST: start game ────────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:start:\d+$"))
async def cb_bunker_start(callback: CallbackQuery, bot: Bot) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)
    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return

    players = await get_bunker_players(session_id)
    if len(players) < 2:
        await callback.answer("⚠️ Потрібно мінімум 2 гравці", show_alert=True)
        return

    session = await start_bunker_game(session_id)

    # Build host cards summary
    players = await get_bunker_players(session_id)
    cards_txt = _cards_summary(players, lang)

    await callback.message.edit_text(
        _status_bar(len(players), session["bunker_capacity"]) + "\n" +
        t("bunker_game_started_host", lang,
          catastrophe=session["catastrophe_text"],
          bunker=session["bunker_text"],
          capacity=session["bunker_capacity"],
          total=len(players),
          cards_summary=cards_txt),
        reply_markup=bunker_host_game_keyboard(session_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()

    # Send each player their private card
    for p in players:
        p_lang = await _get_lang(p["tg_id"])
        card = json.loads(p["card_json"] or "{}")
        card_txt = _card_text(card, p_lang)
        await _push(
            bot, p["tg_id"],
            t("bunker_game_started_player", p_lang,
              catastrophe=session["catastrophe_text"],
              bunker=session["bunker_text"],
              capacity=session["bunker_capacity"],
              total=len(players),
              card=card_txt),
        )


# ─────────────────────── HOST: view cards ────────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:view_cards:\d+$"))
async def cb_bunker_view_cards(callback: CallbackQuery) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)

    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return
    if session["status"] != "active":
        await callback.answer(t("bunker_session_not_active", lang), show_alert=True)
        return

    all_players = await get_bunker_players(session_id)
    alive = [p for p in all_players if p["is_alive"]]
    eliminated = [p for p in all_players if not p["is_alive"]]
    statuses = await get_all_player_statuses(session_id)
    cards_txt = _cards_compact(alive, eliminated, statuses, lang)

    await callback.message.edit_text(
        _status_bar(len(alive), session["bunker_capacity"]) + "\n" +
        t("bunker_cards_view_host", lang,
          alive=len(alive),
          capacity=session["bunker_capacity"],
          cards=cards_txt),
        reply_markup=bunker_host_game_keyboard(session_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────── HOST: open reveal round ─────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:round_open:\d+$"))
async def cb_bunker_round_open(callback: CallbackQuery, bot: Bot) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)

    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return
    if session["status"] != "active":
        await callback.answer(t("bunker_session_not_active", lang), show_alert=True)
        return

    alive = await get_alive_bunker_players(session_id)
    if not alive:
        await callback.answer("⚠️ Немає живих гравців", show_alert=True)
        return
    # Reveal round number = how many attrs the least-revealed player has + 1
    min_revealed = min(len(json.loads(p["revealed"] or "[]")) for p in alive)
    reveal_round = min_revealed + 1

    await update_bunker_session(session_id, current_attr=f"round:{reveal_round}")

    all_players = await get_bunker_players(session_id)
    eliminated = [p for p in all_players if not p["is_alive"]]
    statuses = await get_all_player_statuses(session_id)
    cards_txt = _cards_compact(alive, eliminated, statuses, lang)

    status = _round_status_text(alive, reveal_round, lang)
    await callback.message.edit_text(
        _status_bar(len(alive), session["bunker_capacity"], reveal_round) + "\n" +
        t("bunker_round_open_host", lang, round_num=reveal_round, status=status, cards=cards_txt),
        reply_markup=bunker_host_game_keyboard(session_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()

    # Send each alive player their interactive card keyboard
    for p in alive:
        revealed = json.loads(p["revealed"] or "[]")
        # Skip players who already revealed this round
        if len(revealed) >= reveal_round:
            continue
        p_lang = await _get_lang(p["tg_id"])
        card = json.loads(p["card_json"] or "{}")
        await _push(
            bot, p["tg_id"],
            t("bunker_pick_attr_prompt", p_lang, round_num=reveal_round),
            reply_markup=bunker_player_card_keyboard(session_id, card, revealed, p_lang),
        )


# ─────────────────────── PLAYER: pick attribute (step 1) ─────────────────────

@router.callback_query(F.data.regexp(r"^bunker:pick_attr:\d+:[a-z]+$"))
async def cb_bunker_pick_attr(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    session_id, attr = int(parts[2]), parts[3]
    lang = await _get_lang(callback.from_user.id)

    player = await get_bunker_player(session_id, callback.from_user.id)
    if not player:
        await callback.answer(t("bunker_not_in_session", lang), show_alert=True)
        return

    revealed = json.loads(player["revealed"] or "[]")

    # Round 1: must reveal profession first
    if len(revealed) == 0 and attr != "profession":
        await callback.answer(t("bunker_first_round_profession", lang), show_alert=True)
        return

    if attr in revealed:
        await callback.answer(t("bunker_already_revealed", lang), show_alert=True)
        return

    card = json.loads(player["card_json"] or "{}")
    value = card.get(attr, "—")
    attr_name = t(f"bunker_attr_{attr}", lang)

    # Show value + confirm/back buttons
    await callback.message.answer(
        t("bunker_confirm_attr_prompt", lang, attr_name=attr_name, value=value),
        reply_markup=bunker_player_confirm_keyboard(session_id, attr, lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────── PLAYER: confirm reveal (step 2) ─────────────────────

@router.callback_query(F.data.regexp(r"^bunker:confirm_attr:\d+:[a-z]+$"))
async def cb_bunker_confirm_attr(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    session_id, attr = int(parts[2]), parts[3]
    lang = await _get_lang(callback.from_user.id)

    player = await get_bunker_player(session_id, callback.from_user.id)
    if not player:
        await callback.answer(t("bunker_not_in_session", lang), show_alert=True)
        return

    revealed = json.loads(player["revealed"] or "[]")
    if attr in revealed:
        await callback.answer(t("bunker_already_revealed", lang), show_alert=True)
        return

    # Mark as revealed in DB
    await mark_attr_revealed(session_id, callback.from_user.id, attr)
    await callback.answer(t("bunker_reveal_status_done", lang, name=""), show_alert=False)

    # Disable the confirm keyboard on this message
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Notify host: updated round status + compact cards
    session = await get_bunker_session(session_id)
    if not session:
        return
    host_lang = await _get_lang(session["host_tg_id"])
    alive = await get_alive_bunker_players(session_id)

    current_attr = session.get("current_attr", "")
    reveal_round = int(current_attr.split(":")[-1]) if current_attr.startswith("round:") else 1

    all_players = await get_bunker_players(session_id)
    eliminated = [p for p in all_players if not p["is_alive"]]
    statuses = await get_all_player_statuses(session_id)
    cards_txt = _cards_compact(alive, eliminated, statuses, host_lang)

    status = _round_status_text(alive, reveal_round, host_lang)
    await _push(
        bot, session["host_tg_id"],
        t("bunker_round_status_host", host_lang, round_num=reveal_round, status=status, cards=cards_txt),
    )


# ─────────────────────── PLAYER: back to card selection ──────────────────────

@router.callback_query(F.data.regexp(r"^bunker:back_to_card:\d+$"))
async def cb_bunker_back_to_card(callback: CallbackQuery) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)

    player = await get_bunker_player(session_id, callback.from_user.id)
    if not player:
        await callback.answer(t("bunker_not_in_session", lang), show_alert=True)
        return

    card = json.loads(player["card_json"] or "{}")
    revealed = json.loads(player["revealed"] or "[]")
    reveal_round = len(revealed) + 1

    # Edit the current message to show the card selection again
    await callback.message.edit_text(
        t("bunker_pick_attr_prompt", lang, round_num=reveal_round),
        reply_markup=bunker_player_card_keyboard(session_id, card, revealed, lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────── HOST: open voting ───────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:vote_start:\d+$"))
async def cb_bunker_vote_start(callback: CallbackQuery, bot: Bot) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)

    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return
    if session["status"] != "active":
        await callback.answer(t("bunker_session_not_active", lang), show_alert=True)
        return

    vote_round = session["vote_round"] + 1
    await update_bunker_session(session_id, vote_round=vote_round)

    alive = await get_alive_bunker_players(session_id)
    pending_names = ", ".join(p["display_name"] for p in alive)

    await callback.message.edit_text(
        _status_bar(len(alive), session["bunker_capacity"]) + "\n" +
        t("bunker_vote_open_host", lang, round=vote_round, pending=pending_names),
        reply_markup=bunker_host_game_keyboard(session_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()

    # Send vote keyboard to all alive players
    for p in alive:
        p_lang = await _get_lang(p["tg_id"])
        # Exclude self from vote targets
        targets = [x for x in alive if x["tg_id"] != p["tg_id"]]
        await _push(
            bot, p["tg_id"],
            t("bunker_vote_prompt_player", p_lang),
            reply_markup=bunker_vote_keyboard(session_id, targets, p_lang),
        )


# ─────────────────────── PLAYER: cast vote ───────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:vote:\d+:\d+$"))
async def cb_bunker_vote(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    session_id, target_tg_id = int(parts[2]), int(parts[3])
    lang = await _get_lang(callback.from_user.id)

    session = await get_bunker_session(session_id)
    if not session or session["status"] != "active":
        await callback.answer(t("bunker_session_not_active", lang), show_alert=True)
        return

    vote_round = session["vote_round"]
    ok = await record_bunker_vote(session_id, vote_round, callback.from_user.id, target_tg_id)
    if not ok:
        await callback.answer(t("bunker_already_voted", lang), show_alert=True)
        return

    await callback.answer(t("bunker_vote_cast", lang), show_alert=True)

    # Check if all alive players voted
    pending = await get_pending_vote_players(session_id, vote_round)
    if pending:
        # Notify host: vote progress
        host_lang = await _get_lang(session["host_tg_id"])
        alive = await get_alive_bunker_players(session_id)
        total_alive = len(alive)
        voted = total_alive - len(pending)
        pending_names_map = {p["tg_id"]: p["display_name"] for p in alive}
        pending_str = ", ".join(pending_names_map.get(tid, str(tid)) for tid in pending)
        await _push(
            bot, session["host_tg_id"],
            t("bunker_vote_progress_host", host_lang,
              round=vote_round, voted=voted, total=total_alive, pending=pending_str),
        )
    else:
        # All voted — show results to host
        await _send_vote_results(bot, session_id, vote_round)


async def _send_vote_results(bot: Bot, session_id: int, vote_round: int) -> None:
    session = await get_bunker_session(session_id)
    if not session:
        return
    host_lang = await _get_lang(session["host_tg_id"])
    alive = await get_alive_bunker_players(session_id)
    alive_map = {p["tg_id"]: p["display_name"] for p in alive}

    results = await get_bunker_vote_results(session_id, vote_round)
    result_lines = []
    for target_id, voter_ids in sorted(results.items(), key=lambda x: -len(x[1])):
        name = alive_map.get(target_id, str(target_id))
        voters_str = ", ".join(alive_map.get(v, str(v)) for v in voter_ids)
        result_lines.append(
            t("bunker_vote_result_line", host_lang,
              name=name, votes=len(voter_ids), voters=voters_str)
        )

    # Build candidates list sorted by votes desc for kick keyboard
    candidates = [
        (tid, alive_map.get(tid, str(tid)), len(voters))
        for tid, voters in sorted(results.items(), key=lambda x: -len(x[1]))
    ]

    await _push(
        bot,
        session["host_tg_id"],
        t("bunker_vote_results_host", host_lang,
          round=vote_round,
          results="\n".join(result_lines)),
        reply_markup=bunker_host_kick_keyboard(session_id, candidates, host_lang),
    )


# ─────────────────────── HOST: kick player ───────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:kick:\d+:\d+$"))
async def cb_bunker_kick(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    session_id, target_tg_id = int(parts[2]), int(parts[3])
    lang = await _get_lang(callback.from_user.id)

    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return

    # Get display name before eliminating
    target_player = await get_bunker_player(session_id, target_tg_id)
    if not target_player:
        await callback.answer("⚠️", show_alert=True)
        return
    name = target_player["display_name"]

    await eliminate_bunker_player(session_id, target_tg_id)

    # Notify eliminated player personally
    eliminated_lang = await _get_lang(target_tg_id)
    await _push(bot, target_tg_id, t("bunker_eliminated_player", eliminated_lang))

    # Broadcast round summary to all players (alive + eliminated)
    alive = await get_alive_bunker_players(session_id)
    all_for_broadcast = await get_bunker_players(session_id)
    for p in all_for_broadcast:
        p_lang = await _get_lang(p["tg_id"])
        await _push(
            bot, p["tg_id"],
            t("bunker_kick_summary_broadcast", p_lang,
              vote_round=session["vote_round"],
              eliminated_name=name,
              remaining=len(alive),
              capacity=session["bunker_capacity"]),
        )

    # Check if game should end
    capacity = session["bunker_capacity"]
    if len(alive) <= capacity:
        await _end_game(callback, bot, session_id, lang, auto=True)
        return

    # Update host view
    players_all = await get_bunker_players(session_id)
    alive_remaining = [p for p in players_all if p["is_alive"]]
    cards_txt = _cards_summary(alive_remaining, lang)
    await callback.message.edit_text(
        _status_bar(len(alive_remaining), capacity) + "\n" +
        t("bunker_game_started_host", lang,
          catastrophe=session["catastrophe_text"],
          bunker=session["bunker_text"],
          capacity=capacity,
          total=len(alive_remaining),
          cards_summary=cards_txt),
        reply_markup=bunker_host_game_keyboard(session_id, lang),
        parse_mode="HTML",
    )
    await callback.answer(f"💀 {name} виключено")


@router.callback_query(F.data.regexp(r"^bunker:skip_kick:\d+$"))
async def cb_bunker_skip_kick(callback: CallbackQuery) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)
    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return
    await callback.message.edit_text(
        t("bunker_skip_kick_host", lang),
        reply_markup=bunker_host_game_keyboard(session_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────── HOST: end game ──────────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:end:\d+$"))
async def cb_bunker_end(callback: CallbackQuery, bot: Bot) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)
    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return
    await _end_game(callback, bot, session_id, lang, auto=False)


async def _end_game(
    callback: CallbackQuery, bot: Bot, session_id: int, lang: str, auto: bool
) -> None:
    session = await get_bunker_session(session_id)
    if not session:
        return

    all_players = await get_bunker_players(session_id)
    survivors = [p for p in all_players if p["is_alive"]]
    eliminated = [p for p in all_players if not p["is_alive"]]

    survivors_str = "\n".join(f"  🎉 {p['display_name']}" for p in survivors) or "—"
    eliminated_str = "\n".join(f"  💀 {p['display_name']}" for p in eliminated) or "—"

    await update_bunker_session(session_id, status="ended")

    host_text = t("bunker_game_over_host", lang,
                  survivors=survivors_str, eliminated=eliminated_str)

    try:
        await callback.message.edit_text(host_text, reply_markup=bunker_menu_keyboard(lang), parse_mode="HTML")
    except Exception:
        await _push(bot, session["host_tg_id"], host_text)

    survivor_ids = {p["tg_id"] for p in survivors}
    for p in all_players:
        p_lang = await _get_lang(p["tg_id"])
        if p["tg_id"] in survivor_ids:
            await _push(bot, p["tg_id"],
                        t("bunker_game_over_survivor", p_lang, survivors=survivors_str))
        else:
            await _push(bot, p["tg_id"],
                        t("bunker_game_over_eliminated", p_lang, survivors=survivors_str))

    if auto:
        await callback.answer("🏁 Гра завершена!")
    else:
        await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
#  PHASE 5 — EVENT CARDS (Section 15 of BUNKER_RULES.md)
# ═══════════════════════════════════════════════════════════════════════════════

async def _broadcast_event(bot: Bot, session_id: int, text: str) -> None:
    """Send event broadcast to all alive players."""
    alive = await get_alive_bunker_players(session_id)
    for p in alive:
        await _push(bot, p["tg_id"], text)


# ─────────────────────── HOST: draw event ────────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:draw_event:\d+$"))
async def cb_bunker_draw_event(callback: CallbackQuery, bot: Bot) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)

    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return
    if session["status"] != "active":
        await callback.answer(t("bunker_session_not_active", lang), show_alert=True)
        return

    # No events in final round (when alive == capacity)
    alive = await get_alive_bunker_players(session_id)
    if len(alive) <= session["bunker_capacity"]:
        await callback.answer(t("bunker_event_final_round", lang), show_alert=True)
        return

    # Check for unresolved event
    active_event = await get_active_bunker_event(session_id)
    if active_event:
        await callback.answer(t("bunker_event_already_active", lang), show_alert=True)
        return

    # Cooldown: get last 1 event code to avoid back-to-back repeat
    recent = await get_recent_event_codes(session_id, limit=1)

    # Determine current round
    current_attr = session.get("current_attr", "")
    round_num = int(current_attr.split(":")[-1]) if current_attr.startswith("round:") else 0

    event_code = pick_event(session.get("catastrophe_text", ""), recent)

    if event_code is None:
        await callback.answer(t("bunker_no_event", lang), show_alert=True)
        return

    edef = EVENT_DEFINITIONS.get(event_code, {})
    dc = random.randint(edef.get("dc_min", 12), edef.get("dc_max", 18))
    ename = event_name(event_code, lang)
    etext = event_text(event_code, lang)

    # ── Theft event: special flow ─────────────────────────────────────────────
    if event_code == "theft":
        await _handle_theft_event(
            callback, bot, session, session_id, lang, alive, dc, round_num, ename, etext
        )
        return

    # ── Regular events ────────────────────────────────────────────────────────
    executor, modifier, is_auto = find_executor(event_code, alive)
    is_auto_fail = executor is None and not is_auto

    # Assign sick/breakdown victim for outbreak/psycho
    victim_tg_id = 0
    if event_code in ("outbreak", "psycho"):
        candidates = [p for p in alive if executor is None or p["tg_id"] != executor["tg_id"]]
        if not candidates:
            candidates = alive
        if candidates:
            victim = random.choice(candidates)
            victim_tg_id = victim["tg_id"]
            status = "sick" if event_code == "outbreak" else "breakdown"
            await set_player_status(session_id, victim_tg_id, status)
            # Notify victim privately
            v_lang = await _get_lang(victim_tg_id)
            status_emoji = "🤒" if status == "sick" else "😤"
            await _push(
                bot, victim_tg_id,
                t("bunker_event_victim_status", v_lang,
                  event_name=event_name(event_code, v_lang),
                  status=status_emoji),
            )

    ev = await create_bunker_event(
        session_id, event_code, dc,
        executor_tg_id=executor["tg_id"] if executor else 0,
        modifier=modifier,
        is_auto=1 if is_auto else 0,
        victim_tg_id=victim_tg_id,
        round_num=round_num,
    )

    # Host sees full event card
    executor_name = executor["display_name"] if executor else "—"
    mod_display = "AUTO" if is_auto else (f"+{modifier}" if modifier > 0 else "0")
    special = ""
    if is_auto_fail:
        special = t("bunker_event_no_executor", lang) + "\n\n"
    await callback.message.edit_text(
        t("bunker_event_drawn_host", lang,
          event_name=ename, event_text=etext, dc=dc,
          executor_name=executor_name, modifier=mod_display,
          special=special),
        reply_markup=bunker_host_game_keyboard(session_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()

    # Broadcast event text to all players
    broadcast = t("bunker_event_broadcast", lang, event_name=ename, event_text=etext)
    await _broadcast_event(bot, session_id, broadcast)

    # Auto-resolve immediately
    if is_auto or is_auto_fail:
        outcome = "auto_success" if is_auto else "auto_fail"
        consequence = get_consequence(event_code, outcome, lang)
        await resolve_bunker_event(ev["id"], roll_result=0, outcome=outcome)
        await _apply_event_consequences(bot, session_id, ev["id"], event_code, outcome, alive, session)
        result_text = t("bunker_event_auto_result", lang,
                        event_name=ename, outcome_emoji=_outcome_emoji(outcome),
                        consequence=consequence)
        await _push(bot, session["host_tg_id"], result_text)
        await _broadcast_event(bot, session_id, result_text)
        return

    # Notify executor to roll
    exec_lang = await _get_lang(executor["tg_id"])
    await _push(
        bot, executor["tg_id"],
        t("bunker_event_executor_prompt", exec_lang,
          event_name=event_name(event_code, exec_lang), dc=dc, modifier=modifier),
        reply_markup=bunker_event_roll_keyboard(session_id, ev["id"], exec_lang),
    )


async def _handle_theft_event(
    callback: CallbackQuery,
    bot: Bot,
    session: dict,
    session_id: int,
    lang: str,
    alive: list[dict],
    dc: int,
    round_num: int,
    ename: str,
    etext: str,
) -> None:
    """Handle the special Theft event flow."""
    if len(alive) < 2:
        await callback.answer("⚠️ Мало гравців для крадіжки", show_alert=True)
        return

    detective, det_modifier = find_detective(alive)

    # Pick a random thief (not detective)
    thief_candidates = [p for p in alive if detective is None or p["tg_id"] != detective["tg_id"]]
    if not thief_candidates:
        thief_candidates = alive
    thief = random.choice(thief_candidates)

    ev = await create_bunker_event(
        session_id, "theft", dc,
        executor_tg_id=detective["tg_id"] if detective else 0,
        modifier=det_modifier,
        thief_tg_id=thief["tg_id"],
        round_num=round_num,
    )

    # Host sees full event
    det_name = detective["display_name"] if detective else "—"
    await callback.message.edit_text(
        t("bunker_event_drawn_host", lang,
          event_name=ename, event_text=etext, dc=dc,
          executor_name=det_name,
          modifier=f"+{det_modifier}" if det_modifier > 0 else "0",
          special=t("bunker_theft_host_note", lang)),
        reply_markup=bunker_host_game_keyboard(session_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()

    # Broadcast event to all players
    await _broadcast_event(
        bot, session_id,
        t("bunker_event_broadcast", lang, event_name=ename, event_text=etext),
    )

    # Privately notify thief
    thief_lang = await _get_lang(thief["tg_id"])
    victims = [p for p in alive if p["tg_id"] != thief["tg_id"]]
    await _push(
        bot, thief["tg_id"],
        t("bunker_event_thief_assigned", thief_lang),
        reply_markup=bunker_steal_victim_keyboard(session_id, ev["id"], victims, thief_lang),
    )

    # Notify detective
    if detective:
        det_lang = await _get_lang(detective["tg_id"])
        await _push(
            bot, detective["tg_id"],
            t("bunker_event_detective_assigned", det_lang,
              dc=dc, modifier=det_modifier),
        )


# ─────────────────────── THIEF: pick victim ──────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:steal_victim:\d+:\d+:\d+$"))
async def cb_bunker_steal_victim(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    session_id, event_id, victim_tg_id = int(parts[2]), int(parts[3]), int(parts[4])
    lang = await _get_lang(callback.from_user.id)

    ev = await get_bunker_event(event_id)
    if not ev or ev["is_resolved"] or ev["thief_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return

    victim = await get_bunker_player(session_id, victim_tg_id)
    if not victim:
        await callback.answer("⚠️", show_alert=True)
        return

    # Show victim's revealed attrs to steal
    revealed = json.loads(victim.get("revealed") or "[]")
    if not revealed:
        await callback.answer(
            t("bunker_theft_victim_no_attrs", lang), show_alert=True
        )
        return

    await callback.message.edit_text(
        t("bunker_event_thief_pick_attr", lang, victim_name=victim["display_name"]),
        reply_markup=bunker_steal_attr_keyboard(session_id, event_id, victim_tg_id, revealed, lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────── THIEF: pick attr to steal ───────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:steal_attr:\d+:\d+:\d+:[a-z]+$"))
async def cb_bunker_steal_attr(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    session_id, event_id, victim_tg_id, attr = int(parts[2]), int(parts[3]), int(parts[4]), parts[5]
    lang = await _get_lang(callback.from_user.id)

    ev = await get_bunker_event(event_id)
    if not ev or ev["is_resolved"] or ev["thief_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return

    if ev["stolen_attr"]:
        await callback.answer(t("bunker_theft_already_stolen", lang), show_alert=True)
        return

    victim = await get_bunker_player(session_id, victim_tg_id)
    if not victim:
        await callback.answer("⚠️", show_alert=True)
        return

    # Record the theft
    await update_bunker_event(event_id, victim_tg_id=victim_tg_id, stolen_attr=attr)

    attr_name = t(f"bunker_attr_{attr}", lang)
    await callback.message.edit_text(
        t("bunker_event_theft_done_thief", lang,
          victim_name=victim["display_name"], attr_name=attr_name),
        parse_mode="HTML",
    )
    await callback.answer()

    # Notify detective: now roll
    session = await get_bunker_session(session_id)
    if not session:
        return
    detective_tg_id = ev["executor_tg_id"]
    if detective_tg_id:
        det_lang = await _get_lang(detective_tg_id)
        await _push(
            bot, detective_tg_id,
            t("bunker_detective_roll_prompt", det_lang,
              dc=ev["dc"], modifier=ev["modifier"]),
            reply_markup=bunker_event_roll_keyboard(session_id, event_id, det_lang),
        )
    else:
        # No detective → auto-fail
        host_lang = await _get_lang(session["host_tg_id"])
        outcome = "auto_fail"
        consequence = get_consequence("theft", outcome, host_lang)
        await resolve_bunker_event(event_id, roll_result=0, outcome=outcome)
        alive = await get_alive_bunker_players(session_id)
        await _apply_event_consequences(bot, session_id, event_id, "theft", outcome, alive, session)
        ename = event_name("theft", host_lang)
        result_text = t("bunker_event_auto_result", host_lang,
                        event_name=ename, outcome_emoji=_outcome_emoji(outcome),
                        consequence=consequence)
        await _push(bot, session["host_tg_id"], result_text)
        await _broadcast_event(bot, session_id, result_text)


# ─────────────────────── EXECUTOR / DETECTIVE: roll dice ─────────────────────

@router.callback_query(F.data.regexp(r"^bunker:roll_dice:\d+:\d+$"))
async def cb_bunker_roll_dice(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    session_id, event_id = int(parts[2]), int(parts[3])
    lang = await _get_lang(callback.from_user.id)

    ev = await get_bunker_event(event_id)
    if not ev or ev["is_resolved"]:
        await callback.answer(t("bunker_event_already_resolved", lang), show_alert=True)
        return

    session = await get_bunker_session(session_id)
    if not session:
        return

    # Validate roller: must be executor (or detective for theft)
    if ev["executor_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return

    # For theft: ensure theft has happened
    if ev["event_code"] == "theft" and not ev["stolen_attr"]:
        await callback.answer(t("bunker_theft_wait_thief", lang), show_alert=True)
        return

    roll = roll_d20()
    modifier = ev["modifier"]
    dc = ev["dc"]
    is_auto = bool(ev["is_auto"])
    outcome = resolve_roll(roll, modifier, dc, is_auto, is_auto_fail=False)

    await resolve_bunker_event(event_id, roll_result=roll, outcome=outcome)

    # Disable roll button
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    event_code = ev["event_code"]
    ename = event_name(event_code, lang)
    consequence = get_consequence(event_code, outcome, lang)
    total = roll + modifier

    host_lang = await _get_lang(session["host_tg_id"])
    result_text = t("bunker_event_roll_result", host_lang,
                    executor_name=callback.from_user.full_name or str(callback.from_user.id),
                    roll=roll, modifier=modifier, total=total, dc=dc,
                    outcome_emoji=_outcome_emoji(outcome),
                    consequence=get_consequence(event_code, outcome, host_lang))

    await _push(bot, session["host_tg_id"], result_text)

    alive = await get_alive_bunker_players(session_id)
    broadcast_text = t("bunker_event_roll_result", lang,
                       executor_name=callback.from_user.full_name or str(callback.from_user.id),
                       roll=roll, modifier=modifier, total=total, dc=dc,
                       outcome_emoji=_outcome_emoji(outcome),
                       consequence=get_consequence(event_code, outcome, lang))
    await _broadcast_event(bot, session_id, broadcast_text)
    await callback.answer(f"🎲 {roll}!")

    await _apply_event_consequences(bot, session_id, event_id, event_code, outcome, alive, session)


# ─────────────────────── consequence helpers ─────────────────────────────────

def _outcome_emoji(outcome: str) -> str:
    return {
        "auto_success": "🌟",
        "crit_success": "⚡",
        "success":      "✅",
        "fail":         "❌",
        "crit_fail":    "💀",
        "auto_fail":    "💀",
    }.get(outcome, "❓")


async def _apply_event_consequences(
    bot: Bot,
    session_id: int,
    event_id: int,
    event_code: str,
    outcome: str,
    alive: list[dict],
    session: dict,
) -> None:
    """Apply automatic mechanical consequences based on event + outcome."""
    ev = await get_bunker_event(event_id)
    if not ev:
        return
    capacity = session["bunker_capacity"]

    def _random_alive_except(exclude_id: int) -> dict | None:
        candidates = [p for p in alive if p["tg_id"] != exclude_id]
        return random.choice(candidates) if candidates else (alive[0] if alive else None)

    # ── Outbreak ──────────────────────────────────────────────────────────────
    if event_code == "outbreak":
        victim_id = ev["victim_tg_id"]
        if outcome in ("success", "crit_success", "auto_success"):
            await clear_player_status(session_id, victim_id)
            await set_player_status(session_id, victim_id, "immune")
        elif outcome in ("fail", "crit_fail", "auto_fail"):
            # Infect 1 extra player
            extra = _random_alive_except(victim_id)
            if extra:
                await set_player_status(session_id, extra["tg_id"], "sick")
                lang = await _get_lang(extra["tg_id"])
                await _push(bot, extra["tg_id"],
                            t("bunker_status_infected", lang))
            if outcome == "crit_fail":
                # Infect one more
                extra2 = _random_alive_except(victim_id)
                if extra2 and extra2["tg_id"] != (extra["tg_id"] if extra else -1):
                    await set_player_status(session_id, extra2["tg_id"], "sick")

    # ── Flood ─────────────────────────────────────────────────────────────────
    elif event_code == "flood":
        if outcome in ("fail", "crit_fail", "auto_fail"):
            delta = 2 if outcome in ("crit_fail", "auto_fail") else 1
            new_cap = max(1, capacity - delta)
            await update_bunker_session(session_id, bunker_capacity=new_cap)

    # ── Power ─────────────────────────────────────────────────────────────────
    elif event_code == "power":
        executor_id = ev["executor_tg_id"]
        if outcome in ("success", "crit_success", "auto_success"):
            if executor_id:
                await set_player_status(session_id, executor_id, "repairing")
        else:
            # All get blackout
            for p in alive:
                await set_player_status(session_id, p["tg_id"], "blackout")
            if outcome in ("crit_fail", "auto_fail"):
                sick_target = _random_alive_except(executor_id)
                if sick_target:
                    await set_player_status(session_id, sick_target["tg_id"], "sick")

    # ── Intruder ──────────────────────────────────────────────────────────────
    elif event_code == "intruder":
        if outcome in ("fail", "crit_fail", "auto_fail"):
            new_cap = max(1, capacity - 1)
            await update_bunker_session(session_id, bunker_capacity=new_cap)
            if outcome == "crit_fail":
                sick_target = random.choice(alive) if alive else None
                if sick_target:
                    await set_player_status(session_id, sick_target["tg_id"], "sick")

    # ── Resources ─────────────────────────────────────────────────────────────
    elif event_code == "resources":
        if outcome in ("crit_fail", "auto_fail"):
            sick_target = random.choice(alive) if alive else None
            if sick_target:
                await set_player_status(session_id, sick_target["tg_id"], "sick")

    # ── Psycho ────────────────────────────────────────────────────────────────
    elif event_code == "psycho":
        victim_id = ev["victim_tg_id"]
        if outcome in ("success", "crit_success", "auto_success"):
            await clear_player_status(session_id, victim_id)
        elif outcome == "fail":
            await set_player_status(session_id, victim_id, "skip_turn")
        elif outcome == "crit_fail":
            pass  # 😤 stays permanently (already set)
        elif outcome == "auto_fail":
            # Eliminate without voting
            await eliminate_bunker_player(session_id, victim_id)
            victim = await get_bunker_player(session_id, victim_id)
            name = victim["display_name"] if victim else str(victim_id)
            v_lang = await _get_lang(victim_id)
            await _push(bot, victim_id, t("bunker_eliminated_player", v_lang))
            alive_after = await get_alive_bunker_players(session_id)
            for p in alive_after:
                p_lang = await _get_lang(p["tg_id"])
                await _push(bot, p["tg_id"],
                            t("bunker_eliminated_broadcast", p_lang, name=name))
            # Notify host to check game end manually
            updated_session = await get_bunker_session(session_id)
            if updated_session and len(alive_after) <= updated_session["bunker_capacity"]:
                host_lang = await _get_lang(session["host_tg_id"])
                await _push(
                    bot, session["host_tg_id"],
                    t("bunker_game_auto_end_hint", host_lang),
                )

    # ── Theft ─────────────────────────────────────────────────────────────────
    elif event_code == "theft":
        victim_id = ev["victim_tg_id"]
        stolen_attr = ev["stolen_attr"]
        if victim_id and stolen_attr:
            victim = await get_bunker_player(session_id, victim_id)
            if victim:
                card = json.loads(victim.get("card_json") or "{}")
                revealed = json.loads(victim.get("revealed") or "[]")
                if outcome in ("success", "crit_success"):
                    # Attr is returned — no DB change needed (it was never removed yet)
                    pass
                else:
                    # Attr stolen — remove from victim's card and revealed
                    card.pop(stolen_attr, None)
                    if stolen_attr in revealed:
                        revealed.remove(stolen_attr)
                    await update_bunker_player(
                        session_id, victim_id,
                        card_json=json.dumps(card, ensure_ascii=False),
                        revealed=json.dumps(revealed, ensure_ascii=False),
                    )
                    if outcome == "crit_fail":
                        # Steal one more revealed attr
                        remaining = [a for a in revealed if a != stolen_attr]
                        if remaining:
                            extra_attr = random.choice(remaining)
                            card.pop(extra_attr, None)
                            remaining.remove(extra_attr)
                            await update_bunker_player(
                                session_id, victim_id,
                                card_json=json.dumps(card, ensure_ascii=False),
                                revealed=json.dumps(remaining, ensure_ascii=False),
                            )

    # ── Equipment ─────────────────────────────────────────────────────────────
    elif event_code == "equipment":
        executor_id = ev["executor_tg_id"]
        if outcome in ("success", "crit_success", "auto_success"):
            if executor_id:
                await set_player_status(session_id, executor_id, "repairing")
        elif outcome in ("crit_fail", "auto_fail"):
            new_cap = max(1, capacity - 1)
            await update_bunker_session(session_id, bunker_capacity=new_cap)
        # fail: host decides manually (capacity or rations)


# ─── Player info handlers ────────────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:alive_list:\d+$"))
async def cb_bunker_alive_list(callback: CallbackQuery) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)
    session = await get_bunker_session(session_id)
    if not session or session["status"] != "active":
        await callback.answer(t("bunker_session_not_active", lang), show_alert=True)
        return
    alive = await get_alive_bunker_players(session_id)
    names = "\n".join(f"🟢 {p['display_name']}" for p in alive)
    await callback.answer(
        t("bunker_alive_list_popup", lang, count=len(alive), names=names),
        show_alert=True,
    )


@router.callback_query(F.data.regexp(r"^bunker:my_card:\d+$"))
async def cb_bunker_my_card(callback: CallbackQuery) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)
    session = await get_bunker_session(session_id)
    if not session or session["status"] != "active":
        await callback.answer(t("bunker_session_not_active", lang), show_alert=True)
        return
    player = await get_bunker_player(session_id, callback.from_user.id)
    if not player:
        await callback.answer(t("bunker_not_in_session", lang), show_alert=True)
        return
    card = json.loads(player["card_json"] or "{}")
    revealed = json.loads(player["revealed"] or "[]")
    lines = []
    for attr in _ATTR_KEYS:
        attr_name = t(f"bunker_attr_{attr}", lang)
        value = card.get(attr, "—")
        mark = "✅" if attr in revealed else "🔒"
        lines.append(f"  {mark} {attr_name}: <b>{value}</b>")
    await callback.message.answer(
        t("bunker_my_card_header", lang) + "\n\n" + "\n".join(lines),
        parse_mode="HTML",
        reply_markup=bunker_player_card_keyboard(session_id, card, revealed, lang),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^bunker:history:\d+$"))
async def cb_bunker_history(callback: CallbackQuery) -> None:
    session_id = int(callback.data.split(":")[-1])
    lang = await _get_lang(callback.from_user.id)
    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return
    events = await get_bunker_event_history(session_id, limit=5)
    if not events:
        await callback.answer(t("bunker_history_empty", lang), show_alert=True)
        return
    all_players = await get_bunker_players(session_id)
    name_map = {p["tg_id"]: p["display_name"] for p in all_players}
    lines = []
    for ev in events:
        ename = event_name(ev["event_code"], lang)
        oem = _outcome_emoji(ev["outcome"])
        exec_name = name_map.get(ev["executor_tg_id"], "—") if ev["executor_tg_id"] else "—"
        lines.append(f"{oem} {ename} — {exec_name}")
    await callback.answer(
        t("bunker_history_popup", lang, events="\n".join(lines)),
        show_alert=True,
    )

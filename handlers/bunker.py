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
)
from keyboards.kb import (
    bunker_menu_keyboard,
    bunker_player_count_keyboard,
    bunker_host_waiting_keyboard,
    bunker_host_game_keyboard,
    bunker_player_reveal_keyboard,
    bunker_vote_keyboard,
    bunker_host_kick_keyboard,
    back_to_menu_keyboard,
)
from locales import t
from states.forms import BunkerHostForm, BunkerPlayerForm

router = Router()

_ATTR_KEYS = ["profession", "health", "hobby", "phobia", "baggage", "ability"]


# ─────────────────────── helpers ────────────────────────────────────────────

async def _get_lang(tg_id: int) -> str:
    return await get_user_lang(tg_id)


async def _push(bot: Bot, tg_id: int, text: str, **kwargs) -> None:
    """Send a message to a user, silently ignoring Telegram errors."""
    try:
        await bot.send_message(tg_id, text, parse_mode="HTML", **kwargs)
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logging.warning("bunker push to %s failed: %s", tg_id, e)


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


# ─────────────────────── HOST: reveal round ──────────────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:reveal:[a-z]+:\d+$"))
async def cb_bunker_reveal(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    attr, session_id = parts[2], int(parts[3])
    lang = await _get_lang(callback.from_user.id)

    session = await get_bunker_session(session_id)
    if not session or session["host_tg_id"] != callback.from_user.id:
        await callback.answer("⛔", show_alert=True)
        return
    if session["status"] != "active":
        await callback.answer(t("bunker_session_not_active", lang), show_alert=True)
        return

    await update_bunker_session(session_id, current_attr=attr)
    alive = await get_alive_bunker_players(session_id)
    attr_name = t(f"bunker_attr_{attr}", lang)

    # Build reveal status for host
    status_lines = []
    for p in alive:
        revealed = json.loads(p["revealed"] or "[]")
        if attr in revealed:
            status_lines.append(t("bunker_reveal_status_done", lang, name=p["display_name"]))
        else:
            status_lines.append(t("bunker_reveal_status_waiting", lang, name=p["display_name"]))

    await callback.message.edit_text(
        t("bunker_reveal_round_host", lang,
          attr_name=attr_name,
          status="\n".join(status_lines)),
        reply_markup=bunker_host_game_keyboard(session_id, lang),
        parse_mode="HTML",
    )
    await callback.answer()

    # Prompt each alive player
    for p in alive:
        p_lang = await _get_lang(p["tg_id"])
        p_attr_name = t(f"bunker_attr_{attr}", p_lang)
        await _push(
            bot, p["tg_id"],
            t("bunker_reveal_prompt_player", p_lang, attr_name=p_attr_name),
            reply_markup=bunker_player_reveal_keyboard(session_id, attr, p_lang),
        )


# ─────────────────────── PLAYER: show own attribute ──────────────────────────

@router.callback_query(F.data.regexp(r"^bunker:show_attr:[a-z]+:\d+$"))
async def cb_bunker_show_attr(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    attr, session_id = parts[2], int(parts[3])
    lang = await _get_lang(callback.from_user.id)

    player = await get_bunker_player(session_id, callback.from_user.id)
    if not player:
        await callback.answer(t("bunker_not_in_session", lang), show_alert=True)
        return

    card = json.loads(player["card_json"] or "{}")
    value = card.get(attr, "—")
    attr_name = t(f"bunker_attr_{attr}", lang)

    revealed = json.loads(player["revealed"] or "[]")
    if attr in revealed:
        await callback.answer(t("bunker_already_revealed", lang), show_alert=True)
        return

    await mark_attr_revealed(session_id, callback.from_user.id, attr)
    await callback.message.answer(
        t("bunker_attr_shown", lang, attr_name=attr_name, value=value),
        parse_mode="HTML",
    )
    await callback.answer()

    # Notify host: update reveal status
    session = await get_bunker_session(session_id)
    if not session:
        return
    host_lang = await _get_lang(session["host_tg_id"])
    h_attr_name = t(f"bunker_attr_{attr}", host_lang)
    alive = await get_alive_bunker_players(session_id)
    status_lines = []
    for p in alive:
        rv = json.loads(p["revealed"] or "[]")
        if attr in rv:
            status_lines.append(t("bunker_reveal_status_done", host_lang, name=p["display_name"]))
        else:
            status_lines.append(t("bunker_reveal_status_waiting", host_lang, name=p["display_name"]))
    await _push(
        bot,
        session["host_tg_id"],
        t("bunker_reveal_round_host", host_lang,
          attr_name=h_attr_name,
          status="\n".join(status_lines)),
    )


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
        # Notify host: who hasn't voted yet
        host_lang = await _get_lang(session["host_tg_id"])
        alive = await get_alive_bunker_players(session_id)
        pending_names_map = {p["tg_id"]: p["display_name"] for p in alive}
        pending_str = ", ".join(pending_names_map.get(tid, str(tid)) for tid in pending)
        await _push(
            bot, session["host_tg_id"],
            t("bunker_vote_open_host", host_lang, round=vote_round, pending=pending_str),
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

    # Notify eliminated player
    eliminated_lang = await _get_lang(target_tg_id)
    await _push(bot, target_tg_id, t("bunker_eliminated_player", eliminated_lang))

    # Broadcast to all remaining alive players
    alive = await get_alive_bunker_players(session_id)
    for p in alive:
        p_lang = await _get_lang(p["tg_id"])
        await _push(bot, p["tg_id"],
                    t("bunker_eliminated_broadcast", p_lang, name=name))

    # Check if game should end
    capacity = session["bunker_capacity"]
    if len(alive) <= capacity:
        await _end_game(callback, bot, session_id, lang, auto=True)
        return

    # Update host view
    players_all = await get_bunker_players(session_id)
    cards_txt = _cards_summary([p for p in players_all if p["is_alive"]], lang)
    await callback.message.edit_text(
        t("bunker_game_started_host", lang,
          catastrophe=session["catastrophe_text"],
          bunker=session["bunker_text"],
          capacity=capacity,
          total=len([p for p in players_all if p["is_alive"]]),
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

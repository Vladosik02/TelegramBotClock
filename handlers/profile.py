import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import asyncio

from config import WALLET_IBAN, WALLET_BONUS_PCT, WALLET_TOPUP_TIMEOUT_MIN
from database.db import (
    get_user_lang, get_user,
    save_user_profile,
    get_points_history,
    create_wallet_topup,
    cancel_wallet_topup,
    get_wallet_history,
    get_referrals,
    apply_referral_code,
)
from keyboards.kb import (
    profile_keyboard,
    points_history_keyboard,
    wallet_keyboard,
    referrals_keyboard,
    cancel_keyboard,
)
from locales import t
from states.forms import ProfileForm, WalletForm
from utils.notify import notify_admins

router = Router()

PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,15}$")


# ─── helpers ────────────────────────────────────────────────────────────────

async def _show_profile(event, lang: str, user: dict, edit: bool = True) -> None:
    """Render the main profile screen."""
    name_not_set  = t("profile_name_not_set",  lang)
    phone_not_set = t("profile_phone_not_set", lang)

    name_val  = user.get("saved_name")  or name_not_set
    phone_val = user.get("saved_phone") or phone_not_set

    text = t(
        "profile_title", lang,
        tg_id=user["tg_id"],
        name=name_val,
        phone=phone_val,
        points=user.get("points", 0),
        wallet=user.get("wallet_balance", 0),
        ref_code=user.get("referral_code", "—"),
    )
    kb = profile_keyboard(
        lang,
        saved_name=user.get("saved_name") or "",
        saved_phone=user.get("saved_phone") or "",
        points=user.get("points", 0),
        wallet=user.get("wallet_balance", 0),
    )
    if edit and hasattr(event, "message"):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    elif hasattr(event, "edit_text"):
        await event.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


# ─── Main profile screen ─────────────────────────────────────────────────────

@router.callback_query(F.data.in_({"menu:profile", "profile:main"}))
async def cb_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await get_user_lang(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    await _show_profile(callback, lang, user)
    await callback.answer()


# ─── Edit name ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile:edit_name")
async def cb_edit_name(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(ProfileForm.editing_name)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("profile_enter_name", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ProfileForm.editing_name)
async def msg_profile_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    new_name = message.text.strip() if message.text else ""
    if not new_name:
        await message.answer(t("profile_enter_name", lang), reply_markup=cancel_keyboard(lang), parse_mode="HTML")
        return
    await save_user_profile(message.from_user.id, name=new_name)
    await state.clear()
    await message.answer(t("profile_name_saved", lang), parse_mode="HTML")
    user = await get_user(message.from_user.id)
    await _show_profile(message, lang, user, edit=False)


# ─── Edit phone ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile:edit_phone")
async def cb_edit_phone(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(ProfileForm.editing_phone)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("profile_enter_phone", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ProfileForm.editing_phone)
async def msg_profile_phone(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    phone = message.text.strip() if message.text else ""
    if not phone or not PHONE_RE.match(phone):
        await message.answer(t("profile_phone_invalid", lang), reply_markup=cancel_keyboard(lang), parse_mode="HTML")
        return
    await save_user_profile(message.from_user.id, phone=phone)
    await state.clear()
    await message.answer(t("profile_phone_saved", lang), parse_mode="HTML")
    user = await get_user(message.from_user.id)
    await _show_profile(message, lang, user, edit=False)


# ─── Points history ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile:points")
async def cb_points(callback: CallbackQuery) -> None:
    lang = await get_user_lang(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    await _send_points_history(callback, lang, user.get("points", 0), page=0)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^profile:points_page:(\d+)$"))
async def cb_points_page(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[-1])
    lang = await get_user_lang(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    await _send_points_history(callback, lang, user.get("points", 0), page=page)
    await callback.answer()


async def _send_points_history(callback: CallbackQuery, lang: str, points: int, page: int) -> None:
    history, total = await get_points_history(callback.from_user.id, page=page)
    total_pages = max(1, (total + 7) // 8)

    text = t("points_history_title", lang, points=points)
    if history:
        lines = []
        for row in history:
            date_part = row["created_at"][:10]
            lines.append(t("points_history_row", lang,
                           date=date_part,
                           amount=row["amount"],
                           description=row["description"] or ""))
        text += "\n\n" + "\n".join(lines)
    else:
        text += "\n\n" + t("points_history_empty", lang)

    await callback.message.edit_text(
        text,
        reply_markup=points_history_keyboard(page, total_pages, lang),
        parse_mode="HTML",
    )


# ─── Wallet ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile:wallet")
async def cb_wallet(callback: CallbackQuery) -> None:
    lang = await get_user_lang(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    wallet = user.get("wallet_balance", 0)
    text = t("wallet_title", lang, wallet=wallet, bonus=WALLET_BONUS_PCT)
    await callback.message.edit_text(
        text,
        reply_markup=wallet_keyboard(wallet, WALLET_BONUS_PCT, lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "profile:wallet_history")
async def cb_wallet_history(callback: CallbackQuery) -> None:
    lang = await get_user_lang(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    history = await get_wallet_history(callback.from_user.id)

    wallet = user.get("wallet_balance", 0)
    text = t("wallet_title", lang, wallet=wallet, bonus=WALLET_BONUS_PCT)
    if history:
        lines = []
        for row in history:
            date_part = row["created_at"][:10]
            status_key = "wallet_status_confirmed" if row["status"] == "confirmed" else "wallet_status_pending"
            lines.append(t("wallet_history_row", lang,
                           date=date_part,
                           amount=row["amount"],
                           bonus=row["bonus"],
                           status=t(status_key, lang)))
        text += "\n\n" + "\n".join(lines)
    else:
        text += "\n\n" + t("wallet_history_empty", lang)

    await callback.message.edit_text(
        text,
        reply_markup=wallet_keyboard(wallet, WALLET_BONUS_PCT, lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Wallet top-up (FSM) ─────────────────────────────────────────────────────

async def _auto_cancel_topup(bot, tx_id: int, tg_id: int, lang: str, timeout_sec: int) -> None:
    await asyncio.sleep(timeout_sec)
    result = await cancel_wallet_topup(tx_id)
    if result:
        try:
            await bot.send_message(tg_id, t("wallet_topup_auto_cancelled", lang), parse_mode="HTML")
        except Exception:
            pass


@router.callback_query(F.data == "profile:wallet_topup")
async def cb_wallet_topup(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await get_user_lang(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    saved_name = user.get("saved_name") or ""
    if saved_name:
        # Use saved name as payment comment — skip name entry step
        await state.set_state(WalletForm.entering_amount)
        await state.update_data(lang=lang, name=saved_name)
        await callback.message.edit_text(
            t("wallet_enter_amount", lang, bonus=WALLET_BONUS_PCT),
            reply_markup=cancel_keyboard(lang),
            parse_mode="HTML",
        )
    else:
        await state.set_state(WalletForm.entering_name)
        await state.update_data(lang=lang)
        await callback.message.edit_text(
            t("wallet_enter_name", lang),
            reply_markup=cancel_keyboard(lang),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(WalletForm.entering_name)
async def msg_wallet_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    full_name = message.text.strip() if message.text else ""
    if len(full_name) < 2:
        await message.answer(t("wallet_name_invalid", lang), reply_markup=cancel_keyboard(lang), parse_mode="HTML")
        return
    await state.update_data(name=full_name)
    await state.set_state(WalletForm.entering_amount)
    await message.answer(
        t("wallet_enter_amount", lang, bonus=WALLET_BONUS_PCT),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )


@router.message(WalletForm.entering_amount)
async def msg_wallet_amount(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    raw = message.text.strip() if message.text else ""
    if not raw.isdigit() or int(raw) < 50:
        await message.answer(t("wallet_amount_invalid", lang), reply_markup=cancel_keyboard(lang), parse_mode="HTML")
        return

    amount = int(raw)
    bonus = round(amount * WALLET_BONUS_PCT / 100)
    total = amount + bonus
    tg_id = message.from_user.id
    comment = data.get("name", message.from_user.full_name or str(tg_id))

    tx_id = await create_wallet_topup(tg_id, amount, comment)
    await state.clear()

    # Notify user
    text = t("wallet_topup_created", lang,
             amount=amount, iban=WALLET_IBAN, comment=comment, total=total)
    await message.answer(text, parse_mode="HTML")

    # Notify admins
    admin_text = (
        f"💰 <b>Нова заявка на поповнення #{tx_id}</b>\n\n"
        f"👤 {message.from_user.full_name} (ID: <code>{tg_id}</code>)\n"
        f"💳 Сума: <b>{amount} грн</b>\n"
        f"🎁 Бонус: +{bonus} грн\n"
        f"📊 Всього: <b>{total} грн</b>\n"
        f"📝 Коментар: <code>{comment}</code>\n"
        f"⏰ Дійсна {WALLET_TOPUP_TIMEOUT_MIN} хвилин. Підтвердіть у панелі."
    )
    await notify_admins(message.bot, admin_text)

    # Auto-cancel after timeout
    asyncio.create_task(
        _auto_cancel_topup(message.bot, tx_id, tg_id, lang, WALLET_TOPUP_TIMEOUT_MIN * 60)
    )


# ─── Referrals ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile:referrals")
async def cb_referrals(callback: CallbackQuery) -> None:
    from config import BOT_USERNAME
    lang = await get_user_lang(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    referrals = await get_referrals(callback.from_user.id)

    ref_code = user.get("referral_code", "—")
    if BOT_USERNAME:
        link = t("referrals_link", lang, bot_username=BOT_USERNAME, ref_code=ref_code)
        text = t("referrals_title", lang) + f"\n<code>{link}</code>"
    else:
        text = t("referrals_title", lang) + f"\n<code>{ref_code}</code>"

    if referrals:
        text += "\n\n" + t("referrals_count", lang, count=len(referrals))
        for r in referrals:
            name = r.get("full_name") or r.get("username") or str(r["tg_id"])
            date = r.get("created_at", "")[:10]
            text += "\n" + t("referrals_row", lang, name=name, date=date)
    else:
        text += "\n\n" + t("referrals_empty", lang)

    has_referrer = bool(user.get("referred_by"))
    await callback.message.edit_text(
        text,
        reply_markup=referrals_keyboard(lang, has_referrer=has_referrer),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Enter referral code (FSM) ───────────────────────────────────────────────

@router.callback_query(F.data == "profile:enter_ref")
async def cb_enter_ref(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await get_user_lang(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    if user.get("referred_by"):
        await callback.answer(t("ref_already_set", lang), show_alert=True)
        return
    await state.set_state(ProfileForm.entering_ref_code)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        t("enter_ref_code_prompt", lang),
        reply_markup=cancel_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ProfileForm.entering_ref_code)
async def msg_ref_code(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uk")
    code = (message.text or "").strip()
    result = await apply_referral_code(message.from_user.id, code)
    await state.clear()

    key_map = {
        "ok":          "ref_code_applied",
        "already_set": "ref_already_set",
        "not_found":   "ref_code_not_found",
        "own_code":    "ref_code_own",
    }
    await message.answer(t(key_map.get(result, "ref_code_not_found"), lang), parse_mode="HTML")

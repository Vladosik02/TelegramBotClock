import os

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from database.db import get_user_lang, get_all_instructions, get_instruction
from keyboards.kb import instructions_list_keyboard, instruction_back_keyboard, back_to_menu_keyboard
from locales import t

router = Router()

_PAGE_SIZE = 5


async def _show_instructions_page(callback: CallbackQuery, page: int = 0) -> None:
    """Shared logic for showing the paginated instructions list."""
    lang = await get_user_lang(callback.from_user.id)
    instructions = await get_all_instructions()

    if not instructions:
        text = t("instructions_empty", lang)
        kb   = back_to_menu_keyboard(lang)
        if callback.message.photo or callback.message.document:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await callback.answer()
        return

    total_pages = max(1, (len(instructions) + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    kb = instructions_list_keyboard(instructions, lang, page)

    header = t("instructions_title", lang)
    choose = t("instructions_choose", lang)
    if total_pages > 1:
        text = f"{header}\n📄 {page + 1} / {total_pages}\n\n{choose}"
    else:
        text = f"{header}\n\n{choose}"

    # Photo/document messages can't be edited to text — delete and re-send
    if callback.message.photo or callback.message.document:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:instructions")
async def cb_instructions_menu(callback: CallbackQuery) -> None:
    await _show_instructions_page(callback, page=0)


@router.callback_query(F.data.startswith("instr_page:"))
async def cb_instructions_page(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    await _show_instructions_page(callback, page=page)


@router.callback_query(F.data.startswith("instr:"))
async def cb_instruction_view(callback: CallbackQuery) -> None:
    lang           = await get_user_lang(callback.from_user.id)
    instruction_id = int(callback.data.split(":")[1])
    item           = await get_instruction(instruction_id)

    if not item:
        await callback.answer(t("instruction_not_found", lang), show_alert=True)
        return

    kb      = instruction_back_keyboard(lang)
    caption = f"📖 <b>{item['game_name']}</b>\n\n{item['text_content'] or ''}"
    img_path = item.get("local_image", "")

    # Delete the current list message so the photo appears cleanly
    if img_path and os.path.isfile(img_path):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=FSInputFile(img_path),
            caption=caption,
            reply_markup=kb,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    # Telegram file_id (uploaded via admin panel)
    if item.get("content_type") == "file" and item.get("file_id"):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_document(
            document=item["file_id"],
            caption=f"📖 {item['game_name']}",
            reply_markup=kb,
        )
        await callback.answer()
        return

    # Text-only fallback
    await callback.message.edit_text(caption, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

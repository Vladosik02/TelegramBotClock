from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InputMediaPhoto

from database.db import get_user_lang, get_gallery
from keyboards.kb import gallery_keyboard
from locales import t

router = Router()


@router.callback_query(F.data == "menu:gallery")
async def cb_gallery(callback: CallbackQuery, bot: Bot) -> None:
    lang  = await get_user_lang(callback.from_user.id)
    photos = await get_gallery()

    if not photos:
        await callback.message.edit_text(
            t("gallery_empty", lang),
            reply_markup=gallery_keyboard(lang),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    # Send up to 10 photos as a media group
    batch = photos[:10]
    media = [
        InputMediaPhoto(
            media=p["file_id"],
            caption=p["caption"] or (t("gallery_title", lang) if i == 0 else None),
            parse_mode="HTML",
        )
        for i, p in enumerate(batch)
    ]

    await callback.message.answer_media_group(media)
    await callback.message.answer(
        f"📸 {len(photos)} фото",
        reply_markup=gallery_keyboard(lang),
    )
    await callback.answer()

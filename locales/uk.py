STRINGS: dict[str, str] = {
    # ── Language selection ──
    "choose_language": (
        "🌌 Ласкаво просимо до <b>Game Space \"Clock\"</b>!\n\n"
        "Ми дивимось у космос, стоячи на землі. ✨\n\n"
        "Оберіть мову / Choose language:"
    ),
    "lang_set": "✅ Мову встановлено: Українська 🇺🇦",

    # ── Main menu ──
    "main_menu_text": (
        "⚙️ · · · XII · · · ⚙️\n"
        "   XI ·         · I\n"
        "  X ·  🕰 CLOCK  · II\n"
        "IX · Game Space  · III\n"
        "  VIII ·         · IV\n"
        "   VII ·         · V\n"
        "⚙️ · · ·  VI  · · ⚙️\n\n"
        "Ласкаво просимо! 🌿\n"
        "Відпочивайте та грайте на повну!\n\n"
        "📅 Пн–Вт, Чт–Нд: 13:00 – 23:00\n"
        "🗓 Середа — вихідний\n\n"
        "⚡ Генератор · 💧 Вода · 🛡 Безпека\n\n"
        "Оберіть розділ:"
    ),
    "btn_booking":      "📅 Забронювати",
    "btn_birthday":     "🎂 День народження",
    "btn_suggestions":  "💡 Пропозиції",
    "btn_gallery":      "📸 Фото",
    "btn_games":        "🎮 Ігри",
    "btn_instructions": "📖 Настолки",
    "btn_profile":      "👤 Мій профіль",
    "btn_back":         "◀️ Назад",
    "btn_main_menu":    "🏠 Головне меню",
    "btn_cancel":       "❌ Скасувати",
    "btn_confirm":      "✅ Підтвердити",

    # ── Booking ──
    "booking_title": (
        "📅 <b>Бронювання</b>\n\n"
        "✨ <b>Чому варто обрати нас:</b>\n"
        "🍕 Можна приходити зі своєю їжею та напоями\n"
        "🛡 Ви завжди в безпеці\n"
        "🎵 Автентична музика\n"
        "🍵 Безкоштовні чай, вода, зарядка, Wi-Fi\n"
        "🎲 Завжди є чим зайнятися\n\n"
        "Оберіть зону:"
    ),
    "booking_date":    "📆 Введіть дату бронювання:\n<i>Приклад: 15.03.2026</i>",
    "booking_time": (
        "⏰ Вкажіть час початку та закінчення:\n"
        "<i>Формат: 13:00 - 16:00\n"
        "Години роботи: 13:00 — 23:00\n"
        "13:00–18:00 → 100 грн/ос/год · 18:00–23:00 → 150 грн/ос/год</i>"
    ),
    "booking_people":  "👥 Скільки людей? Введіть кількість:",
    "booking_name":    "👤 Введіть ваше ім'я:",
    "booking_phone":   "📱 Введіть номер телефону:\n<i>Приклад: +380501234567</i>",
    "booking_payment": "💳 Оберіть спосіб оплати:",
    "payment_iban":    "🏦 IBAN (онлайн-переказ)",
    "payment_cash":    "💵 Готівка в закладі (протягом 3 днів)",
    "booking_confirm": (
        "📋 <b>Перевірте дані бронювання:</b>\n\n"
        "🎯 Зона: <b>{zone}</b>\n"
        "📆 Дата: <b>{date}</b>\n"
        "⏰ Початок: <b>{time}</b>\n"
        "💰 Тариф: <b>{price}</b>\n"
        "👥 Людей: <b>{people}</b>\n"
        "👤 Ім'я: <b>{name}</b>\n"
        "📱 Телефон: <b>{phone}</b>\n"
        "💳 Оплата: <b>{payment}</b>\n\n"
        "Все вірно?"
    ),
    "booking_success": (
        "✅ <b>Бронювання прийнято!</b> 🚀\n\n"
        "Менеджер зв'яжеться з вами найближчим часом для підтвердження.\n"
        "📞 Мінімальний час — 30 хв."
    ),
    "booking_cancelled": "❌ Бронювання скасовано.",

    # ── Birthday ──
    "birthday_success": (
        "✅ <b>Заявку прийнято!</b> 🎉\n\n"
        "🌌 Менеджер зв'яжеться з вами найближчим часом.\n"
        "Очікуйте на дзвінок або повідомлення!"
    ),
    "birthday_cancelled": "❌ Заявку скасовано.",

    # Birthday flow steps
    "bday_time_pick": (
        "⏰ <b>Вибери час початку свята</b>\n\n"
        "☀️ <i>День</i> · 🌙 <i>Вечір</i>\n"
        "Час роботи: 13:00 — 23:00"
    ),
    "bday_time_pick_end": (
        "⏰ <b>Вибери час завершення свята</b>\n\n"
        "Початок: <b>{start}</b> — обери коли закінчуємо:"
    ),
    "bday_enter_name": (
        "👤 <b>Як звати іменинника/ицю?</b>\n\n"
        "<i>Напишіть ім'я:</i>"
    ),
    "bday_enter_age": (
        "🎂 <b>Скільки виповнюється років?</b>\n\n"
        "<i>Введіть число:</i>"
    ),
    "bday_age_invalid": "⚠️ Введіть число від 1 до 120.",
    "bday_gender_pick_kid": (
        "🎀 <b>Хто іменинник?</b>\n\n"
        "Обери або пропусти:"
    ),
    "bday_gender_pick_adult": (
        "✨ <b>Стать іменинника/ниці?</b>\n\n"
        "Обери або пропусти:"
    ),
    "bday_btn_boy":   "🧒 Хлопчик",
    "bday_btn_girl":  "👧 Дівчинка",
    "bday_btn_man":   "👨 Чоловік",
    "bday_btn_woman": "👩 Дівчина",
    "bday_btn_skip":  "⏭️ Пропустити",
    "bday_enter_color": (
        "🎨 <b>Який улюблений колір?</b>\n\n"
        "<i>Це допоможе визначитись з подарунком!</i>"
    ),
    "bday_enter_phone": (
        "📱 <b>Номер мобільного для зв'язку:</b>\n\n"
        "<i>Приклад: +380501234567</i>"
    ),
    "bday_enter_wishes": (
        "💬 <b>Побажання та ідеї для свята:</b>\n\n"
        "<i>Чи є особливі прохання? Напишіть або надішліть «-» якщо немає.</i>"
    ),
    "bday_payment_summary": (
        "🎉 <b>Майже готово!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>Ваша заявка:</b>\n"
        "📅 Дата: <b>{date}</b>\n"
        "⏰ Час: <b>{time}</b>\n"
        "👤 Ім'я: <b>{name}</b>\n"
        "🎂 Вік: <b>{age}</b>\n"
        "⚥ Стать: <b>{gender}</b>\n"
        "🎨 Колір: <b>{color}</b>\n"
        "📱 Телефон: <b>{phone}</b>\n"
        "💬 Побажання: <b>{wishes}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 Передоплата для підтвердження: <b>{deposit} грн</b>\n\n"
        "🎮 <b>Бонус іменинника/ниці:</b> VR-окуляри <b>безкоштовно</b> 🎁\n\n"
        "Оберіть спосіб оплати:"
    ),
    "bday_btn_iban": "🏦 Передоплата на IBAN",
    "bday_btn_cash": "💵 Готівка протягом 3 днів",
    "bday_success_iban": (
        "✅ <b>Заявку прийнято!</b> 🚀\n\n"
        "🏦 <b>Надішліть {deposit} грн на IBAN:</b>\n"
        "<code>{iban}</code>\n\n"
        "📌 У коментарі вкажіть: «<b>ДН {name} {date}</b>»\n\n"
        "🌌 Менеджер підтвердить бронювання після отримання оплати!"
    ),
    "bday_success_iban_no_iban": (
        "✅ <b>Заявку прийнято!</b> 🚀\n\n"
        "🏦 Менеджер надішле реквізити для передоплати {deposit} грн.\n\n"
        "🌌 Очікуйте на повідомлення!"
    ),
    "bday_success_cash": (
        "✅ <b>Заявку прийнято!</b> 🎉\n\n"
        "💵 Принесіть <b>{deposit} грн готівкою</b> до закладу "
        "протягом <b>3 днів</b> для підтвердження.\n\n"
        "🌌 Менеджер зв'яжеться з вами найближчим часом!"
    ),

    # ── Suggestions ──
    "suggestions_title":   (
        "💡 <b>Пропозиції та побажання</b>\n\n"
        "✨ Ваша думка допомагає нам ставати кращими!\n"
        "Напишіть своє повідомлення:"
    ),
    "suggestions_success": "✅ Дякуємо! Ваша пропозиція отримана. 🚀",
    "suggestions_cancel":  "❌ Скасовано.",

    # ── Gallery ──
    "gallery_title": "📸 <b>Фото Game Space \"Clock\"</b>",
    "gallery_empty": (
        "📸 Фото поки що завантажуються...\n\n"
        "Заходьте пізніше або підписуйтесь на наш канал!"
    ),

    # ── Games ──
    "games_menu":      "🎮 <b>Ігри</b>\n\n🕹 Оберіть платформу:",
    "btn_ps5_games":   "🎮 PlayStation 5",
    "btn_ps4_games":   "🕹 PlayStation 4",
    "ps5_games_title": "🎮 <b>Ігри PlayStation 5</b>",
    "ps4_games_title": "🕹 <b>Ігри PlayStation 4</b>",
    "games_empty":     "🎮 Список ігор поповнюється. Зверніться до менеджера для актуального переліку.",

    # ── Instructions ──
    "instructions_title":    "📖 <b>Настільні ігри</b>",
    "instructions_empty":    "📖 Інструкції додаються. Зверніться до персоналу — ми завжди допоможемо! ✨",
    "instructions_choose":   "Обери гру щоб переглянути правила:",
    "instruction_not_found": "⚠️ Інструкція не знайдена.",

    # ── Profile ──
    "profile_title": (
        "👤 <b>Мій профіль</b>\n\n"
        "🆔 ID: <code>{tg_id}</code>\n"
        "👤 Ім'я: <b>{name}</b>\n"
        "📱 Телефон: <b>{phone}</b>\n\n"
        "⭐ Балів: <b>{points}</b>\n"
        "💰 Гаманець: <b>{wallet} грн</b>\n"
        "🔗 Реф. код: <code>{ref_code}</code>"
    ),
    "profile_name_not_set":   "не вказано",
    "profile_phone_not_set":  "не вказано",
    "btn_edit_name":          "✏️ Ім'я: {name}",
    "btn_edit_phone":         "📱 Телефон: {phone}",
    "btn_points":             "⭐ {points} балів",
    "btn_wallet":             "💰 Гаманець: {wallet} грн",
    "btn_referrals":          "🔗 Мої реферали",
    "btn_change_lang":        "🌐 Змінити мову",
    "profile_enter_name":     "👤 Введіть нове ім'я:",
    "profile_name_saved":     "✅ Ім'я збережено!",
    "profile_enter_phone":    "📱 Введіть новий номер телефону:\n<i>Приклад: +380501234567</i>",
    "profile_phone_saved":    "✅ Телефон збережено!",
    "profile_phone_invalid":  "⚠️ Невірний формат. Введіть номер:\n<i>Приклад: +380501234567</i>",

    # ── Points history ──
    "points_history_title":  (
        "⭐ <b>Мої бали</b>\n\n"
        "Поточний баланс: <b>{points} балів</b>\n\n"
        "Історія нарахувань:"
    ),
    "points_history_empty":  "⭐ Балів поки що немає. Бронюйте — нараховуємо 10% від суми!",
    "points_history_row":    "{date}  <b>+{amount} ⭐</b>  {description}",
    "btn_points_history":    "📋 Історія балів",

    # ── Wallet ──
    "wallet_title": (
        "💰 <b>Гаманець</b>\n\n"
        "Баланс: <b>{wallet} грн</b>\n\n"
        "Поповніть гаманець — отримайте <b>+{bonus}%</b> бонус!"
    ),
    "wallet_topup_btn":             "💳 Поповнити гаманець",
    "wallet_history_btn":           "📋 Історія поповнень",
    "wallet_enter_name": (
        "📝 <b>Введіть ваше ім'я та прізвище</b>\n\n"
        "Ці дані будуть використані як коментар до банківського переказу:"
    ),
    "wallet_name_invalid":          "⚠️ Введіть ім'я та прізвище (мінімум 2 символи):",
    "wallet_enter_amount": (
        "💳 <b>Поповнення гаманця</b>\n\n"
        "Введіть суму поповнення (грн):\n"
        "<i>Мінімум 50 грн. Бонус +{bonus}% нараховується після підтвердження.</i>"
    ),
    "wallet_amount_invalid":        "⚠️ Введіть ціле число не менше 50:",
    "wallet_topup_created": (
        "✅ <b>Заявку на поповнення створено!</b>\n\n"
        "💳 Надішліть <b>{amount} грн</b> на IBAN:\n"
        "<code>{iban}</code>\n\n"
        "📝 <b>Коментар до платежу</b> (скопіюйте одним кліком):\n"
        "<code>{comment}</code>\n\n"
        "⚠️ Заявка дійсна <b>30 хвилин</b>. Якщо кошти не надійдуть — скасується автоматично.\n\n"
        "Після підтвердження — <b>{total} грн</b> (з бонусом) буде зараховано."
    ),
    "wallet_topup_auto_cancelled": (
        "⏰ <b>Заявку на поповнення скасовано.</b>\n\n"
        "30 хвилин минуло без підтвердження. Якщо ви здійснили переказ — зверніться до менеджера."
    ),
    "wallet_topup_confirmed": (
        "✅ <b>Поповнення підтверджено!</b>\n\n"
        "💰 Зараховано: <b>{total} грн</b>\n"
        "🎁 (включаючи бонус {bonus} грн)"
    ),
    "wallet_history_empty":         "💰 Поповнень поки що немає.",
    "wallet_history_row":           "{date}  <b>{amount} грн</b>  +{bonus} бонус  {status}",
    "wallet_status_pending":        "⏳ очікує",
    "wallet_status_confirmed":      "✅ підтверджено",

    # ── Referrals ──
    "referrals_title": (
        "🔗 <b>Мої реферали</b>\n\n"
        "Запроси друга — отримай <b>3%</b> від його трат за місяць!\n\n"
        "Ваше реферальне посилання:"
    ),
    "referrals_link":            "https://t.me/{bot_username}?start={ref_code}",
    "referrals_empty":           "👥 У вас поки що немає рефералів.",
    "referrals_count":           "👥 Ваших рефералів: <b>{count}</b>",
    "referrals_row":             "• {name} — з {date}",
    "btn_enter_ref_code":        "🔗 Ввести реферальний код",
    "enter_ref_code_prompt":     "🔗 Введіть реферальний код друга:",
    "ref_code_applied":          "✅ Реферальний код прийнято! Тепер ви пов'язані з вашим реферером.",
    "ref_already_set":           "ℹ️ Ви вже були запрошені іншим користувачем.",
    "ref_code_not_found":        "❌ Такого коду не знайдено. Перевірте правильність і спробуйте ще раз.",
    "ref_code_own":              "❌ Не можна ввести власний реферальний код.",

    # ── Use saved value in booking ──
    "use_saved_name_prompt":     "👤 В профілі збережено ім'я:\n<b>{name}</b>\n\nВикористати?",
    "use_saved_phone_prompt":    "📱 В профілі збережено номер:\n<b>{phone}</b>\n\nВикористати?",
    "btn_use_saved_name":        "✅ Використати: {name}",
    "btn_use_saved_phone":       "✅ Використати: {phone}",
    "btn_enter_other_name":      "✏️ Інше ім'я",
    "btn_enter_other_phone":     "✏️ Інший номер",

    # ── Points awarded ──
    "points_awarded":            "⭐ Нараховано <b>{amount} балів</b>!",

    # ── Admin: wallet topups ──
    "btn_wallet_topups":         "💰 Поповнення",
    "admin_topups_title":        "💰 <b>Заявки на поповнення</b>\n\nОберіть для деталей:",
    "no_pending_topups":         "💰 Нових заявок немає.",
    "topup_detail": (
        "💰 <b>Заявка #{id}</b>\n\n"
        "👤 {name} (ID: <code>{tg_id}</code>)\n"
        "💳 Сума: <b>{amount} грн</b>\n"
        "🎁 Бонус: +{bonus} грн\n"
        "📊 Всього: <b>{total} грн</b>\n"
        "📝 Коментар: <code>{comment}</code>\n"
        "📅 {date}"
    ),
    "btn_confirm_topup":         "✅ Підтвердити поповнення",
    "btn_cancel_topup":          "❌ Відхилити",
    "topup_confirmed_ok":        "✅ Поповнення підтверджено! {total} грн зараховано.",
    "topup_cancelled_ok":        "✅ Заявку відхилено.",
    "wallet_topup_rejected": (
        "❌ <b>Вашу заявку на поповнення {amount} грн відхилено адміністратором.</b>\n\n"
        "Якщо ви вже здійснили переказ — зверніться до менеджера."
    ),

    # ── Admin: referral bonuses ──
    "btn_ref_bonuses":           "🔗 Реф. бали",
    "admin_ref_confirm": (
        "🔗 <b>Нарахувати реферальні бали</b>\n\n"
        "Місяць: <b>{month_name} {year}</b>\n\n"
        "Система нарахує реферерам 3% від витрат їхніх рефералів за цей місяць.\n\n"
        "Продовжити?"
    ),
    "admin_ref_done": (
        "✅ <b>Реферальні бали нараховані!</b>\n\n"
        "Реферерів: <b>{referrers}</b>\n"
        "Всього балів: <b>{total_points}</b>"
    ),
    "btn_ref_bonuses_confirm":   "✅ Нарахувати",

    # ── Admin ──
    "not_admin":      "⛔ Немає доступу.",
    "admin_panel":    "⚙️ <b>Адмін-панель</b>\n\nОберіть дію:",
    "btn_admin_panel":      "⚙️ Адмін-панель",
    "btn_add_game":         "➕ Гру",
    "btn_add_photo":        "➕ Фото",
    "btn_add_instruction":  "➕ Інструкцію",
    "btn_bookings_list":    "📋 Бронювання",
    "btn_birthday_list":    "🎂 Заявки ДН",
    "btn_stats":            "📊 Статистика",
    "btn_add_booking":      "➕ Бронювання",
    "btn_users":            "👥 Юзери",
    "btn_broadcast":        "📢 Розсилка",
    "btn_confirm_booking":  "✅ Підтвердити",
    "btn_cancel_booking":   "❌ Скасувати",
    "btn_delete_entry":     "🗑 Видалити запис",
    "entry_deleted_ok":     "🗑 Запис видалено.",
    "btn_block_user":       "🚫 Заблокувати",
    "btn_unblock_user":     "✅ Розблокувати",
    "btn_broadcast_send":   "📤 Розіслати всім",
    "admin_game_platform":  "Оберіть платформу:",
    "admin_game_title":     "Введіть назву гри:",
    "admin_game_image":     "Надішліть фото обкладинки (або /skip щоб пропустити):",
    "admin_game_added":     "✅ Гру додано!",
    "admin_photo_send":     "Надішліть фото для галереї:",
    "admin_photo_caption":  "Введіть підпис до фото (або /skip):",
    "admin_photo_added":    "✅ Фото додано до галереї!",
    "admin_instr_name":     "Введіть назву гри для інструкції:",
    "admin_instr_content":  "Надішліть текст або файл інструкції:",
    "admin_instr_added":    "✅ Інструкцію додано!",
    "no_bookings":          "Бронювань немає.",
    "no_birthday_orders":   "Заявок на ДН немає.",
    "no_users":             "Користувачів немає.",
    "not_found":            "❌ Не знайдено.",
    "admin_bookings_title": "📋 <b>Бронювання</b>\n\nОберіть для деталей:",
    "admin_birthdays_title":"🎂 <b>Заявки — Дні народження</b>\n\nОберіть для деталей:",
    "admin_users_title":    "👥 <b>Користувачі</b>\n\n• Всього: <b>{total}</b>  • Заблоковано: <b>{blocked}</b>\n\nОберіть для деталей:",
    "booking_confirmed_ok":     "✅ Бронювання підтверджено!",
    "booking_cancelled_ok":     "❌ Бронювання скасовано!",
    "booking_confirmed_notify": "✅ <b>Ваше бронювання #{id} підтверджено!</b>\n\nЧекаємо на вас! 🚀",
    "booking_cancelled_notify": "❌ <b>Ваше бронювання #{id} скасовано.</b>\n\nПитання? @Clock_Anticafe",
    "birthday_confirmed_notify":"✅ <b>Вашу заявку ДН #{id} підтверджено!</b>\n\nЧекаємо на свято! 🎉",
    "birthday_cancelled_notify":"❌ <b>Вашу заявку ДН #{id} скасовано.</b>\n\nПитання? @Clock_Anticafe",
    "user_blocked_ok":      "🚫 Користувача заблоковано.",
    "user_unblocked_ok":    "✅ Користувача розблоковано.",
    "you_are_blocked":      "🚫 <b>Ваш акаунт тимчасово заблоковано.</b>\n\nПитання? @Clock_Anticafe",
    "admin_add_booking_zone":   "📋 <b>Нове бронювання (адмін)</b>\n\nОберіть зону:",
    "admin_add_booking_notes":  "📝 Коментар до бронювання (або /skip):",
    "admin_add_booking_done":   "✅ <b>Бронювання #{id} створено та підтверджено!</b>",
    "admin_broadcast_enter":    (
        "📢 <b>Розсилка</b>\n\n"
        "Введіть текст повідомлення.\n"
        "Підтримується HTML-форматування (<b>жирний</b>, <i>курсив</i>):"
    ),
    "admin_broadcast_empty":    "⚠️ Порожнє повідомлення. Введіть текст:",
    "admin_broadcast_preview":  (
        "📢 <b>Попередній перегляд розсилки</b>\n\n"
        "Отримувачів: <b>{count}</b>\n\n"
        "━━━━━━━━━━━━\n"
        "{text}\n"
        "━━━━━━━━━━━━\n\n"
        "Розіслати?"
    ),
    "admin_broadcast_sending":  "⏳ Розсилаємо {count} користувачам...",
    "admin_broadcast_done":     "✅ <b>Розсилка завершена!</b>\n\n📤 Відправлено: <b>{sent}</b>\n❌ Помилок: <b>{failed}</b>",

    # ── Misc ──
    "invalid_people": "⚠️ Введіть ціле число (наприклад: 3)",
    "cancelled":      "❌ Дію скасовано.",
    "booking_birthday_conflict": (
        "🎂 <b>Цей час зайнятий Днем Народження</b>\n\n"
        "У вибраний проміжок у нас проходить приватне свято.\n"
        "Будь ласка, обери інший час або зверніться до адміністратора: @Clock_Anticafe"
    ),

    # ── Bunker Game ──
    "btn_bunker": "🎲 Бункер",

    "bunker_menu_title": (
        "🎲 <b>Бункер</b>\n\n"
        "Постапокаліптична гра на виживання.\n"
        "Ведучий керує грою, гравці отримують таємні карточки та борються за місце в бункері.\n\n"
        "<i>Від 4 до 12 гравців.</i>"
    ),
    "bunker_btn_create":         "🚀 Створити гру",
    "bunker_btn_join":           "🔑 Приєднатись",
    "bunker_btn_start_game":     "▶️ Розпочати гру",
    "bunker_btn_cancel_session": "❌ Скасувати сесію",
    "bunker_btn_vote":           "🗳 Голосування",
    "bunker_btn_end_game":       "🏁 Завершити гру",
    "bunker_btn_reveal_round":   "▶ Розпочати раунд розкриття",
    "bunker_btn_confirm_reveal": "✅ Оголошую вголос",
    "bunker_btn_back_to_card":   "← Змінити вибір",
    "bunker_btn_skip_kick":      "⏭ Нікого не виключати",

    "bunker_select_count": (
        "🎲 <b>Створення гри «Бункер»</b>\n\n"
        "Скільки гравців буде грати?\n"
        "<i>(Ти — ведучий, не рахуєшся)</i>"
    ),
    "bunker_session_created": (
        "✅ <b>Сесія створена!</b>\n\n"
        "📋 Код гри: <code>{code}</code>\n"
        "👥 Очікуємо гравців: {joined}/{max}\n\n"
        "Повідом гравцям код — вони вводять його в боті.\n"
        "Коли всі зайдуть — натисни <b>▶️ Розпочати гру</b>."
    ),
    "bunker_waiting_update": (
        "⏳ <b>Очікування гравців</b>\n\n"
        "📋 Код: <code>{code}</code>\n"
        "👥 Підключились: {joined}/{max}\n\n"
        "{player_list}"
    ),
    "bunker_enter_code": (
        "🔑 <b>Приєднатись до гри</b>\n\n"
        "Введи 6-значний код, який повідомив ведучий:"
    ),
    "bunker_code_not_found": "❌ Сесію з таким кодом не знайдено або вона вже завершена.",
    "bunker_session_full":   "⚠️ Сесія вже заповнена.",
    "bunker_already_joined": "ℹ️ Ти вже в цій сесії.",
    "bunker_joined": (
        "✅ <b>Ти в бункері!</b>\n\n"
        "📋 Код: <code>{code}</code>\n"
        "⏳ Очікуй, поки ведучий розпочне гру…"
    ),
    "bunker_already_host": "⚠️ Ти вже є ведучим активної сесії.",

    "bunker_game_started_host": (
        "🌋 <b>ГРА РОЗПОЧАТА!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "☢️ <b>КАТАСТРОФА:</b>\n{catastrophe}\n\n"
        "🏠 <b>БУНКЕР:</b>\n{bunker}\n\n"
        "👥 Місць у бункері: <b>{capacity}</b> з {total}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🃏 <b>Карточки гравців:</b>\n{cards_summary}\n\n"
        "<i>Натисни «▶ Розпочати розкриття» — гравці самі оберуть, що показати.</i>"
    ),
    "bunker_game_started_player": (
        "🌋 <b>ГРА РОЗПОЧАТА!</b>\n\n"
        "☢️ <b>Катастрофа:</b> {catastrophe}\n\n"
        "🏠 Є бункер на <b>{capacity}</b> осіб з {total}.\n"
        "Тільки найкращі виживуть!\n\n"
        "🃏 <b>Твоя таємна карточка:</b>\n{card}"
    ),
    "bunker_card_line":          "  {attr}: <b>{value}</b>",

    "bunker_round_open_host": (
        "📋 <b>Раунд розкриття #{round_num}</b>\n\n"
        "Гравці обирають, що розкрити. Очікуй поки всі оголосять!\n\n"
        "{status}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🃏 <b>Картки:</b>\n{cards}"
    ),
    "bunker_round_status_host": (
        "📋 <b>Раунд #{round_num} — оновлення</b>\n\n"
        "{status}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🃏 <b>Картки:</b>\n{cards}"
    ),
    "bunker_pick_attr_prompt": (
        "🃏 <b>Раунд #{round_num} — обери атрибут</b>\n\n"
        "Натисни на той атрибут, який хочеш оголосити сьогодні.\n"
        "<i>✅ = вже розкрито  •  🔓 = можна розкрити</i>"
    ),
    "bunker_confirm_attr_prompt": (
        "👁 <b>Ти обрав: {attr_name}</b>\n\n"
        "Твоє значення: 🎴 <b>{value}</b>\n\n"
        "<i>Запам'ятай і оголоси вголос решті гравців!\n"
        "Після підтвердження атрибут буде зафіксовано.</i>"
    ),
    "bunker_first_round_profession": "⚠️ У першому раунді всі зобов'язані розкрити Профессію!",
    "bunker_already_revealed": "ℹ️ Ти вже розкривав цей атрибут.",
    "bunker_reveal_status_done":    "✅ {name}",
    "bunker_reveal_status_waiting": "⏳ {name}",

    "bunker_vote_open_host": (
        "🗳 <b>ГОЛОСУВАННЯ #{round}</b>\n\n"
        "Гравці голосують анонімно.\n"
        "Чекай поки всі проголосують…\n\n"
        "Не проголосували: {pending}"
    ),
    "bunker_vote_prompt_player": (
        "🗳 <b>ГОЛОСУВАННЯ!</b>\n\n"
        "Кого виключити з бункера?\n"
        "<i>Голос анонімний — ведучий побачить результати після всіх.</i>"
    ),
    "bunker_vote_cast":     "✅ Голос прийнято. Очікуй результатів.",
    "bunker_already_voted": "ℹ️ Ти вже проголосував у цьому раунді.",
    "bunker_vote_results_host": (
        "📊 <b>Результати голосування #{round}:</b>\n\n"
        "{results}\n\n"
        "Кого виключаємо?"
    ),
    "bunker_vote_result_line": "<b>{name}</b> — {votes} голос.: {voters}",

    "bunker_eliminated_player": (
        "💀 <b>Тебе виключили з бункера.</b>\n\n"
        "Ти залишаєшся назовні…\n"
        "Спостерігай за грою — може, переможці ще роздумають? 👀"
    ),
    "bunker_eliminated_broadcast": "💀 <b>{name}</b> покидає бункер!",
    "bunker_skip_kick_host": "⏭ Раунд голосування пропущено. Ніхто не виключений.",

    "bunker_game_over_host": (
        "🏆 <b>ГРА ЗАВЕРШЕНА!</b>\n\n"
        "🎉 Виживші:\n{survivors}\n\n"
        "💀 Залишились назовні:\n{eliminated}\n\n"
        "<i>Дякуємо за гру в Game Space Clock! 🚀</i>"
    ),
    "bunker_game_over_survivor": (
        "🏆 <b>ТИ ВИЖИВ!</b>\n\n"
        "Вітаємо — твоє місце в бункері забезпечене! 🎉\n\n"
        "Виживші: {survivors}"
    ),
    "bunker_game_over_eliminated": (
        "💀 <b>Гра завершена.</b>\n\n"
        "Виживші: {survivors}\n\n"
        "<i>Наступного разу пощастить! 🌌</i>"
    ),
    "bunker_session_cancelled": "❌ Сесію скасовано ведучим.",
    "bunker_no_active_session":  "ℹ️ У тебе немає активної сесії.",
    "bunker_not_in_session":     "ℹ️ Ти не є учасником цієї гри.",
    "bunker_session_not_active": "ℹ️ Гра ще не розпочата або вже завершена.",

    # Attribute display names
    "bunker_attr_profession": "💼 Професія",
    "bunker_attr_health":     "❤️ Здоров'я",
    "bunker_attr_hobby":      "🎯 Хобі",
    "bunker_attr_phobia":     "😨 Фобія",
    "bunker_attr_baggage":    "🎒 Багаж",
    "bunker_attr_ability":    "⚡ Здібність",
    "bunker_attr_age":        "🎂 Вік",

    # Rules button
    "bunker_btn_rules": "📖 Правила гри",

    # Rules text (uses Telegram expandable blockquote)
    "bunker_rules": (
        "📖 <b>ПРАВИЛА ГРИ «БУНКЕР»</b>\n\n"

        "🎯 <b>Мета</b>\n"
        "<blockquote expandable>"
        "Сталась катастрофа. Є бункер — але місць менше, ніж людей.\n\n"
        "Кожен отримує таємну карточку з 6 характеристиками:\n"
        "💼 Професія · ❤️ Здоров'я · 🎯 Хобі\n"
        "😨 Фобія · 🎒 Багаж · ⚡ Здібність\n\n"
        "Переконай інших що ти потрібен бункеру. Виживають не всі."
        "</blockquote>\n\n"

        "🔄 <b>Хід гри</b>\n"
        "<blockquote expandable>"
        "1. Ведучий зачитує вголос катастрофу та опис бункера — бот підготує текст.\n\n"
        "2. Ведучий оголошує раунд розкриття атрибута (наприклад: «Всі відкривають Професію»).\n\n"
        "3. Кожен гравець натискає кнопку в боті — бот показує значення особисто.\n"
        "   Гравець оголошує його вголос і аргументує свою цінність.\n\n"
        "4. Після кількох раундів розкриття — ведучий запускає голосування.\n\n"
        "5. Крок 2–4 повторюється до тих пір, поки в живих не залишиться рівно стільки гравців, скільки місць у бункері."
        "</blockquote>\n\n"

        "🗳 <b>Голосування</b>\n"
        "<blockquote expandable>"
        "Коли ведучий відкриває голосування:\n\n"
        "• Кожен гравець анонімно голосує в боті за того, кого хоче виключити.\n"
        "• Бот збирає всі голоси і показує результат тільки ведучому.\n"
        "• Ведучий оголошує вголос: «За Олега проголосували — Таня, Вася та Женя».\n"
        "• Потім просить підняти руку тих, хто голосував.\n\n"
        "Хто не підняв руку — збрехав. Це частина гри 👀\n\n"
        "Ведучий сам вирішує кого виключати — кнопки в боті для підтвердження."
        "</blockquote>\n\n"

        "⚖️ <b>Спірні ситуації</b>\n"
        "<blockquote expandable>"
        "<b>Рівна кількість голосів?</b>\n"
        "Претенденти отримують по 30 секунд на переконання — потім повторне голосування. "
        "Якщо знову нічия — ведучий вирішує одноосібно або нікого не виключають (кнопка «⏭ Нікого не виключати»).\n\n"
        "<b>Можна брехати про свою карточку?</b>\n"
        "Так — але тільки вголос. Бот фіксує справжнє значення. "
        "Якщо тебе спіймають на брехні — це аргумент для виключення.\n\n"
        "<b>Чи можна не розкривати атрибут?</b>\n"
        "Ні — якщо ведучий оголосив раунд, всі зобов'язані натиснути кнопку і оголосити значення.\n\n"
        "<b>Хворий / вагітна / інвалід — одразу мінус?</b>\n"
        "Не обов'язково. Ветеринар із діабетом може бути кориснішим за здорового юриста — залежить від бункера і катастрофи."
        "</blockquote>\n\n"

        "🏁 <b>Кінець гри</b>\n"
        "<blockquote expandable>"
        "Гра закінчується коли кількість живих гравців дорівнює кількості місць у бункері.\n\n"
        "Ведучий натискає «🏁 Завершити гру» — бот надсилає кожному підсумок:\n"
        "переможцям — вітання, решті — красиве прощання 💀\n\n"
        "Після гри відкрийте всі карточки і розкажіть хто насправді був ким — "
        "це найцікавіший момент: коли виявляється що «лікар» насправді був безробітним блогером 😅"
        "</blockquote>"
    ),

    # ── Phase 5: Event Cards (Section 15) ────────────────────────────────────
    "bunker_btn_view_cards":       "🃏 Картки гравців",
    "bunker_cards_view_host": (
        "🃏 <b>Картки гравців</b>\n"
        "👥 Живих: <b>{alive}</b>  /  🏠 Місць: <b>{capacity}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "{cards}"
    ),
    "bunker_cards_nothing_revealed": "нічого не розкрито",

    "bunker_btn_draw_event":      "🎲 Витягнути подію",
    "bunker_btn_roll_dice":       "🎲 Кинути кубик",

    "bunker_no_event":            "🎲 Цього разу тихо. Подія не відбулася.",
    "bunker_event_final_round":   "🏁 У фінальному раунді події заборонені.",
    "bunker_event_already_active": "⚠️ Є незавершена подія! Спершу вирішіть її.",
    "bunker_event_already_resolved": "ℹ️ Ця подія вже завершена.",

    "bunker_event_drawn_host": (
        "🎲 <b>ПОДІЯ: {event_name}</b>\n\n"
        "<blockquote>{event_text}</blockquote>\n\n"
        "⚙️ DC: <b>{dc}</b>\n"
        "👤 Виконавець: <b>{executor_name}</b>\n"
        "🎯 Модифікатор: <b>{modifier}</b>\n\n"
        "{special}"
        "<i>Зачитай картку вголос. Виконавець отримав кнопку «Кинути кубик».</i>"
    ),
    "bunker_event_broadcast": (
        "⚠️ <b>ПОДІЯ: {event_name}</b>\n\n"
        "{event_text}"
    ),
    "bunker_event_executor_prompt": (
        "🎯 <b>Ти призначений виконавцем!</b>\n\n"
        "Подія: <b>{event_name}</b>\n"
        "DC: <b>{dc}</b> | Твій бонус: <b>+{modifier}</b>\n\n"
        "Натисни кнопку коли будеш готовий кинути кубик."
    ),
    "bunker_event_no_executor": "⚠️ <b>Нема підходящого виконавця — Автопровал!</b>\n\n",
    "bunker_event_auto_result": (
        "{outcome_emoji} <b>{event_name}</b>\n\n"
        "{consequence}"
    ),
    "bunker_event_roll_result": (
        "🎲 <b>{executor_name} кидає кубик!</b>\n\n"
        "Кидок: <b>{roll}</b>\n"
        "Модифікатор: <b>+{modifier}</b>\n"
        "Разом: <b>{total}</b> vs DC <b>{dc}</b>\n\n"
        "{outcome_emoji} {consequence}"
    ),

    # Theft event
    "bunker_theft_host_note":     "🎭 <b>Злодія призначено таємно. Слідчий вже в курсі.</b>\n\n",
    "bunker_event_thief_assigned": (
        "🎭 <b>Ти — таємний злодій!</b>\n\n"
        "Обери гравця, у якого хочеш вкрасти вже розкритий атрибут.\n"
        "<i>Тільки ти бачиш це повідомлення.</i>"
    ),
    "bunker_event_detective_assigned": (
        "🔍 <b>Ти — слідчий!</b>\n\n"
        "Злодій діє прямо зараз. Коли він завершить — ти отримаєш кнопку для кидка.\n"
        "DC: <b>{dc}</b> | Твій бонус: <b>+{modifier}</b>"
    ),
    "bunker_event_thief_pick_attr": (
        "🎭 <b>Жертва: {victim_name}</b>\n\n"
        "Який розкритий атрибут вкрадеш?"
    ),
    "bunker_event_theft_done_thief": (
        "✅ <b>Крадіжку здійснено!</b>\n\n"
        "Жертва: {victim_name}\n"
        "Атрибут: {attr_name}\n\n"
        "<i>Очікуй дій слідчого…</i>"
    ),
    "bunker_detective_roll_prompt": (
        "🔍 <b>Злодій діяв! Час розслідування.</b>\n\n"
        "DC: <b>{dc}</b> | Твій бонус: <b>+{modifier}</b>\n\n"
        "Натисни кнопку щоб кинути кубик."
    ),
    "bunker_theft_victim_no_attrs":  "ℹ️ У цього гравця ще немає розкритих атрибутів.",
    "bunker_theft_already_stolen":   "ℹ️ Крадіжку вже здійснено.",
    "bunker_theft_wait_thief":       "⏳ Очікуй поки злодій зробить крадіжку.",

    # Status notifications
    "bunker_event_victim_status": (
        "⚠️ <b>Подія: {event_name}</b>\n\n"
        "Ти отримуєш статус {status}\n"
        "<i>Тільки ти знаєш про це. Результат залежить від виконавця.</i>"
    ),
    "bunker_status_infected":     "🤒 Ти заразився! Статус: 🤒 Хворий.",
    "bunker_game_auto_end_hint":  "🏁 <b>Підказка:</b> Живих гравців = місць у бункері. Можна завершувати гру кнопкою «🏁 Завершити гру».",

    # --- UI improvements ---
    "bunker_btn_history":    "📜 Історія",
    "bunker_btn_alive_list": "👥 Хто живий",
    "bunker_btn_my_card":    "🃏 Моя карта",
    "bunker_vote_progress_host": (
        "🗳 <b>ГОЛОСУВАННЯ #{round}</b>\n\n"
        "Проголосували: {voted}/{total}\n"
        "Ще не голосували: {pending}"
    ),
    "bunker_kick_summary_broadcast": (
        "⚔️ <b>Раунд {vote_round} завершено</b>\n\n"
        "💀 Вибув: <b>{eliminated_name}</b>\n"
        "🟢 Живих: {remaining} | 🏠 Місця: {capacity}"
    ),
    "bunker_alive_list_popup": "🟢 Живих: {count}\n\n{names}",
    "bunker_my_card_header":   "🃏 <b>Твоя карта:</b>",
    "bunker_history_empty":    "📜 Подій ще не було.",
    "bunker_history_popup":    "📜 <b>Останні події:</b>\n\n{events}",
}

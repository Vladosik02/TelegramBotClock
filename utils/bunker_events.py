"""Bunker game event system — Section 15 of BUNKER_RULES.md.

Event Cards: 8 types, D20+DC mechanics, player statuses, consequence logic.
Pure Python only — no async/DB code here.
"""
import json
import random

# ─── Catastrophe tag detection ────────────────────────────────────────────────

_TAG_PATTERNS = [
    (["ядерна зима", "ядерной зим", "третя світова", "третья мировая"], "nuclear_winter"),
    (["химера", "хімера", "пандемі"], "pandemic"),
    (["астероїд", "астероид", "апофіс", "апофис"], "asteroid"),
    (["бунт машин", "іі-систем", "ші-систем", "дрони-охоронц", "дроны-охранник"], "machine_revolt"),
    (["сонячний спалах", "солнечная вспышка", "клас x", "класса x"], "solar_flare"),
    (["гриби-паразит", "кордицепс", "грибы-паразит"], "fungal"),
    (["глобальне потепл", "глобальное потеп", "рівень океану", "уровень океана"], "climate"),
    (["позаземний вірус", "внеземной вирус", "марсу із зараж", "с марса с заражён"], "alien_virus"),
    (["хімічна катастрофа", "химическая катастрофа", "токсична хмара"], "chemical"),
    (["магнітного поля", "магнитного поля", "озоновий шар"], "magnetic"),
    (["нанороботи", "нанороботы", "сіра слиз", "серая слизь"], "nanobots"),
    (["землетрус", "землетрясение", "тектоніч", "тектоничес"], "earthquake"),
    (["вторгнення прибульц", "вторжение пришельц", "флот з 4000", "флот из 4000"], "invasion"),
    (["генетичн зброя", "генетическ оружие", "генетичну зброю", "генетического оружия"], "genetic"),
    (["загибель флори", "гибель флоры", "рослинності зникл"], "flora_death"),
]


def detect_catastrophe_tag(text: str) -> str:
    """Detect catastrophe type tag from scenario text."""
    low = text.lower()
    for patterns, tag in _TAG_PATTERNS:
        if any(p in low for p in patterns):
            return tag
    return "unknown"


# ─── Probability tables (section 15.5, 15.7) ─────────────────────────────────

# Base chance per round (%) that ANY event fires
EVENT_BASE_CHANCE: dict[str, int] = {
    "pandemic": 35, "fungal": 35,
    "genetic": 30, "alien_virus": 30,
    "nuclear_winter": 25, "chemical": 25, "climate": 25, "invasion": 25,
    "asteroid": 20, "machine_revolt": 20, "solar_flare": 20,
    "flora_death": 20, "earthquake": 20,
    "magnetic": 15, "nanobots": 15,
    "unknown": 20,
}

# Per-event-code weight per catastrophe tag (section 15.7)
EVENT_PROBS: dict[str, dict[str, int]] = {
    "nuclear_winter":  {"flood": 25, "intruder": 20, "resources": 30, "psycho": 25, "theft": 20, "equipment": 25},
    "pandemic":        {"outbreak": 35, "intruder": 25, "resources": 25, "psycho": 35, "theft": 20},
    "asteroid":        {"flood": 30, "power": 20, "intruder": 20, "resources": 25, "psycho": 25, "theft": 20, "equipment": 20},
    "machine_revolt":  {"power": 35, "resources": 20, "psycho": 25, "theft": 25, "equipment": 35},
    "solar_flare":     {"power": 35, "intruder": 20, "resources": 25, "psycho": 25, "theft": 20, "equipment": 20},
    "fungal":          {"outbreak": 35, "intruder": 25, "resources": 25, "psycho": 35, "theft": 20},
    "climate":         {"flood": 30, "intruder": 25, "resources": 30, "psycho": 25, "theft": 20},
    "alien_virus":     {"outbreak": 30, "intruder": 20, "resources": 20, "psycho": 30, "theft": 20},
    "chemical":        {"flood": 25, "intruder": 20, "resources": 25, "psycho": 25, "theft": 20},
    "magnetic":        {"intruder": 15, "resources": 20, "psycho": 15, "theft": 15, "equipment": 15},
    "nanobots":        {"resources": 25, "psycho": 15, "theft": 15, "equipment": 15},
    "earthquake":      {"flood": 35, "power": 20, "intruder": 20, "resources": 25, "psycho": 25, "theft": 20, "equipment": 25},
    "invasion":        {"flood": 20, "power": 20, "intruder": 25, "resources": 25, "psycho": 30, "theft": 25, "equipment": 20},
    "genetic":         {"outbreak": 30, "intruder": 20, "resources": 25, "psycho": 35, "theft": 20},
    "flora_death":     {"intruder": 20, "resources": 35, "psycho": 20, "theft": 20},
    "unknown":         {"intruder": 20, "resources": 20, "psycho": 20, "theft": 15},
}

# ─── Consequence texts ────────────────────────────────────────────────────────

_C: dict[str, dict[str, str]] = {
    "outbreak": {
        "success_uk":      "✅ Хворий одужує — статус 💊. Наступного раунду повернеться до норми.",
        "success_ru":      "✅ Больной выздоравливает — статус 💊. В следующем раунде вернётся в норму.",
        "crit_success_uk": "⚡ Критичний успіх! Хворий вилікований миттєво і стає героєм раунду!",
        "crit_success_ru": "⚡ Критический успех! Больной вылечен мгновенно. Исполнитель — герой раунда!",
        "fail_uk":         "❌ Провал. Хворий 🤒 залишається. Ще 1 гравець отримує 🤒 (зараження).",
        "fail_ru":         "❌ Провал. Больной 🤒 остаётся. Ещё 1 игрок получает 🤒 (заражение).",
        "crit_fail_uk":    "💀 Критичний провал! Двоє гравців отримують 🤒.",
        "crit_fail_ru":    "💀 Критический провал! Двое игроков получают 🤒.",
        "auto_fail_uk":    "💀 Автопровал — немає медиків! Двоє гравців отримують 🤒.",
        "auto_fail_ru":    "💀 Автопровал — нет медиков! Двое игроков получают 🤒.",
    },
    "flood": {
        "success_uk":      "✅ Пошкодження усунені. Бункер у безпеці.",
        "success_ru":      "✅ Повреждения устранены. Бункер в безопасности.",
        "crit_success_uk": "⚡ Критичний успіх! Зміцнено весь периметр. Виконавець незамінний!",
        "crit_success_ru": "⚡ Критический успех! Укреплён весь периметр. Исполнитель незаменим!",
        "fail_uk":         "❌ Провал. Місткість бункера -1. Одним місцем менше!",
        "fail_ru":         "❌ Провал. Вместимость бункера -1. Одним местом меньше!",
        "crit_fail_uk":    "💀 Критичний провал! Місткість -2. Аварійний стан!",
        "crit_fail_ru":    "💀 Критический провал! Вместимость -2. Аварийное состояние!",
        "auto_fail_uk":    "💀 Автопровал! Місткість -2. Ніхто не зміг зупинити затоплення.",
        "auto_fail_ru":    "💀 Автопровал! Вместимость -2. Никто не смог остановить затопление.",
    },
    "power": {
        "success_uk":      "✅ Живлення відновлено. Виконавець отримує статус 🛠️.",
        "success_ru":      "✅ Питание восстановлено. Исполнитель получает статус 🛠️.",
        "crit_success_uk": "⚡ Критичний успіх! Генератор оптимізовано — майбутній раунд без небезпек.",
        "crit_success_ru": "⚡ Критический успех! Генератор оптимизирован — следующий раунд без опасностей.",
        "fail_uk":         "❌ Провал. Всі гравці отримують ⚡ на 1 раунд. Вентиляція ослаблена.",
        "fail_ru":         "❌ Провал. Все игроки получают ⚡ на 1 раунд. Вентиляция ослаблена.",
        "crit_fail_uk":    "💀 Критичний провал! ⚡ для всіх + 1 гравець отримує 🤒 (задуха).",
        "crit_fail_ru":    "💀 Критический провал! ⚡ для всех + 1 игрок получает 🤒 (удушье).",
        "auto_fail_uk":    "💀 Автопровал! ⚡ для всіх + 1 гравець 🤒 від задухи.",
        "auto_fail_ru":    "💀 Автопровал! ⚡ для всех + 1 игрок 🤒 от удушья.",
    },
    "intruder": {
        "success_uk":      "✅ Незвану особу усунуто. Ситуація під контролем.",
        "success_ru":      "✅ Незваный гость устранён. Ситуация под контролем.",
        "crit_success_uk": "⚡ Критичний успіх! Особа нейтралізована бездоганно. Авторитет виконавця зріс.",
        "crit_success_ru": "⚡ Критический успех! Незваный гость нейтрализован безупречно.",
        "fail_uk":         "❌ Провал. Особа лишається — місткість -1, ресурси -10%.",
        "fail_ru":         "❌ Провал. Гость остаётся — вместимость -1, ресурсы -10%.",
        "crit_fail_uk":    "💀 Критичний провал! Особа агресивна — місткість -1 + 1 гравець 🤒.",
        "crit_fail_ru":    "💀 Критический провал! Гость агрессивен — вместимость -1 + 1 игрок 🤒.",
        "auto_fail_uk":    "💀 Автопровал! Особа захоплює ресурси — місткість -1.",
        "auto_fail_ru":    "💀 Автопровал! Незваный гость захватывает ресурсы — вместимость -1.",
    },
    "resources": {
        "success_uk":      "✅ Запаси стабілізовані. Ситуація під контролем.",
        "success_ru":      "✅ Запасы стабилизированы. Ситуация под контролем.",
        "crit_success_uk": "⚡ Критичний успіх! Знайдено додаткові запаси. Раціон збільшено!",
        "crit_success_ru": "⚡ Критический успех! Найдены дополнительные запасы. Рацион увеличен!",
        "fail_uk":         "❌ Провал. Раціон -30% на 2 раунди. Всі відчуватимуть нестачу.",
        "fail_ru":         "❌ Провал. Рацион -30% на 2 раунда. Все почувствуют нехватку.",
        "crit_fail_uk":    "💀 Критичний провал! Раціон -50% + 1 гравець 🤒 від виснаження.",
        "crit_fail_ru":    "💀 Критический провал! Рацион -50% + 1 игрок 🤒 от истощения.",
        "auto_fail_uk":    "💀 Автопровал! Раціон -50% + 1 гравець 🤒. Нікому не до їжі.",
        "auto_fail_ru":    "💀 Автопровал! Рацион -50% + 1 игрок 🤒. Никому не до еды.",
    },
    "psycho": {
        "success_uk":      "✅ Кризу подолано — статус 😤 знімається.",
        "success_ru":      "✅ Кризис преодолён — статус 😤 снимается.",
        "crit_success_uk": "⚡ Критичний успіх! Гравець стабілізований і навіть налаштований краще ніж раніше.",
        "crit_success_ru": "⚡ Критический успех! Игрок стабилизирован и даже настроен лучше, чем раньше.",
        "fail_uk":         "❌ Провал. Гравець зі 😤 пропускає аргументацію наступного раунду (статус 🚫).",
        "fail_ru":         "❌ Провал. Игрок с 😤 пропускает аргументацию следующего раунда (статус 🚫).",
        "crit_fail_uk":    "💀 Критичний провал! Гравець зі 😤 лишається з ним постійно.",
        "crit_fail_ru":    "💀 Критический провал! Игрок с 😤 остаётся с ним постоянно.",
        "auto_fail_uk":    "💀 АВТОПРОВАЛ! Психоз некерований — гравець ВИКЛЮЧАЄТЬСЯ БЕЗ ГОЛОСУВАННЯ!",
        "auto_fail_ru":    "💀 АВТОПРОВАЛ! Психоз неуправляем — игрок ИСКЛЮЧАЕТСЯ БЕЗ ГОЛОСОВАНИЯ!",
    },
    "theft": {
        "success_uk":      "🔍 Злодій викритий! Вкрадений атрибут повертається жертві.",
        "success_ru":      "🔍 Вор раскрыт! Украденный атрибут возвращается жертве.",
        "crit_success_uk": "⚡ Критичний успіх! Злодій публічно викритий. Авторитет слідчого зріс.",
        "crit_success_ru": "⚡ Критический успех! Вор публично разоблачён. Авторитет следователя вырос.",
        "fail_uk":         "❌ Провал. Злодій непійманий. Вкрадений атрибут зникає назавжди.",
        "fail_ru":         "❌ Провал. Вор не пойман. Украденный атрибут исчезает навсегда.",
        "crit_fail_uk":    "💀 Критичний провал! Злодій іде і краде ще один атрибут у тієї ж жертви.",
        "crit_fail_ru":    "💀 Критический провал! Вор уходит и крадёт ещё один атрибут у той же жертвы.",
        "auto_fail_uk":    "💀 Немає слідчого! Злодій безкарний. Атрибут зникає назавжди.",
        "auto_fail_ru":    "💀 Нет следователя! Вор безнаказан. Атрибут исчезает навсегда.",
        "no_theft_uk":     "ℹ️ Злодій не зробив крадіжки. Подія завершена без наслідків.",
        "no_theft_ru":     "ℹ️ Вор не совершил кражи. Событие завершено без последствий.",
    },
    "equipment": {
        "success_uk":      "✅ Система відновлена. Виконавець — герой раунду! 🛠️",
        "success_ru":      "✅ Система восстановлена. Исполнитель — герой раунда! 🛠️",
        "crit_success_uk": "⚡ Критичний успіх! Система відновлена та покращена. Виконавець незамінний!",
        "crit_success_ru": "⚡ Критический успех! Система восстановлена и улучшена. Исполнитель незаменим!",
        "fail_uk":         "❌ Провал. Місткість -1 або раціон -20% (ведучий вирішує).",
        "fail_ru":         "❌ Провал. Вместимость -1 или рацион -20% (ведущий решает).",
        "crit_fail_uk":    "💀 Критичний провал! Місткість -1 І раціон -20% одночасно.",
        "crit_fail_ru":    "💀 Критический провал! Вместимость -1 И рацион -20% одновременно.",
        "auto_fail_uk":    "💀 Автопровал! Місткість -1 + раціон -20%. Катастрофічне пошкодження!",
        "auto_fail_ru":    "💀 Автопровал! Вместимость -1 + рацион -20%. Катастрофическое повреждение!",
    },
}

# ─── Event definitions ────────────────────────────────────────────────────────
# matchers: list of (attr_type, [keywords], modifier)
#   modifier = "auto" → auto-success if any keyword matches
#   modifier = int    → roll bonus

EVENT_DEFINITIONS: dict[str, dict] = {
    "outbreak": {
        "name_uk": "🦠 Спалах інфекції",
        "name_ru": "🦠 Вспышка инфекции",
        "text_uk": "У бункері хтось захворів. Температура, нудота, слабкість. Якщо не вжити заходів — зараза поширюється.",
        "text_ru": "В бункере кто-то заболел. Температура, тошнота, слабость. Если не принять меры — зараза распространяется.",
        "dc_min": 12, "dc_max": 18,
        "assigns_sick": True,
        "matchers": [
            ("profession", ["лікар", "хірург", "терапевт", "педіатр", "акушер", "стоматолог", "лікар-хірург", "врач", "хирург"], "auto"),
            ("profession", ["медсестр", "медбрат", "фельдшер", "парамедик"], 5),
            ("profession", ["поліцейськ", "рятуваль", "пожежник", "перша допомога"], 2),
            ("hobby",      ["медицин", "медик", "перша допомога", "фармацевт"], 2),
            ("baggage",    ["аптечк", "ліки", "антибіотик", "медикам", "шприц", "бинт", "вакцин"], 1),
        ],
        "consequences": _C["outbreak"],
    },
    "flood": {
        "name_uk": "💧 Затоплення",
        "name_ru": "💧 Затопление",
        "text_uk": "Тріщина в стіні. Вода або токсичний газ просочується. Якщо не полагодити — втратимо секцію бункера.",
        "text_ru": "Трещина в стене. Вода или токсичный газ просачивается. Если не починить — потеряем секцию бункера.",
        "dc_min": 13, "dc_max": 19,
        "assigns_sick": False,
        "matchers": [
            ("profession", ["інженер-будівельник", "будівельник", "механік", "сантехнік", "геолог", "гірник"], 5),
            ("profession", ["архітектор", "водопровідник", "слюсар"], 3),
            ("hobby",      ["будівництв", "ремонт", "слюсар", "diy"], 2),
            ("baggage",    ["інструмент", "цемент", "дриль", "молоток", "ізолент", "цвяхи"], 1),
        ],
        "consequences": _C["flood"],
    },
    "power": {
        "name_uk": "⚡ Відключення живлення",
        "name_ru": "⚡ Отключение питания",
        "text_uk": "Генератор замовчав. Немає освітлення. Вентиляція — 30% потужності. Є хвилини на рішення.",
        "text_ru": "Генератор замолчал. Нет освещения. Вентиляция — 30% мощности. Есть минуты на решение.",
        "dc_min": 11, "dc_max": 17,
        "assigns_sick": False,
        "matchers": [
            ("profession", ["електрик", "електротехнік", "енергетик"], "auto"),
            ("profession", ["it-фахівець", "технік", "програміст", "системний адмін", "радіоаматор", "інженер"], 4),
            ("hobby",      ["електроніка", "радіоаматор", "diy", "схемотехніка"], 2),
            ("baggage",    ["ліхтар", "кабель", "дизель", "акумулятор", "генератор", "батарейки"], 1),
        ],
        "consequences": _C["power"],
    },
    "intruder": {
        "name_uk": "🚪 Незвана особа",
        "name_ru": "🚪 Незваный гость",
        "text_uk": "Хтось знайшовся в бункері — проник або ховався з початку. Виглядає пригнічено, але може стати загрозою.",
        "text_ru": "Кто-то обнаружился в бункере — проник или прятался с начала. Выглядит подавленно, но может стать угрозой.",
        "dc_min": 10, "dc_max": 16,
        "assigns_sick": False,
        "matchers": [
            ("profession", ["психолог", "дипломат", "юрист", "переговорн"], 5),
            ("profession", ["солдат", "військов", "поліцейськ", "охоронець", "спецназ", "боксер"], 4),
            ("hobby",      ["бойов", "єдиноборств", "борьб", "карат", "бокс", "стрільб"], 3),
            ("baggage",    ["зброя", "пістолет", "ніж", "сокир", "рушниц"], 3),
        ],
        "consequences": _C["intruder"],
    },
    "resources": {
        "name_uk": "🥫 Криза ресурсів",
        "name_ru": "🥫 Кризис ресурсов",
        "text_uk": "Ревізія: запасів менше, ніж рахувалось. Раціон скорочується. Хтось може врятувати ситуацію?",
        "text_ru": "Ревизия: запасов меньше, чем считалось. Паёк сокращается. Кто-то может исправить ситуацию?",
        "dc_min": 12, "dc_max": 18,
        "assigns_sick": False,
        "matchers": [
            ("profession", ["агроном", "ботанік", "фермер", "садівник", "рільник"], "auto"),
            ("profession", ["кухар", "нутриціолог", "кулінар", "кондитер"], 4),
            ("profession", ["економіст", "логіст", "менеджер", "бухгалтер"], 3),
            ("hobby",      ["садівництв", "консервац", "рибальств", "полювання", "кулінарія", "городник"], 2),
            ("baggage",    ["насіння", "добрив", "рибацьке", "вудка", "консерви", "запаси їжі"], 2),
        ],
        "consequences": _C["resources"],
    },
    "psycho": {
        "name_uk": "🧠 Психологічний зрив",
        "name_ru": "🧠 Психологический срыв",
        "text_uk": "Один із мешканців на межі. Плач, агресія, ступор. Якщо не допомогти — ситуація погіршиться для всіх.",
        "text_ru": "Один из обитателей на грани. Плач, агрессия, ступор. Если не помочь — ситуация ухудшится для всех.",
        "dc_min": 11, "dc_max": 17,
        "assigns_breakdown": True,
        "matchers": [
            ("profession", ["психолог", "психотерапевт", "психіатр"], "auto"),
            ("profession", ["соціальний праців", "педагог", "вчитель", "соціолог"], 4),
            ("profession", ["лікар", "медсестр", "фельдшер"], 3),
            ("baggage",    ["антидепресант", "заспокійлив", "ліки", "аптечк"], 2),
        ],
        "consequences": _C["psycho"],
    },
    "theft": {
        "name_uk": "🔍 Зрада / Крадіжка",
        "name_ru": "🔍 Предательство / Кража",
        "text_uk": "Хтось таємно бере більше, ніж належить. Пайки не сходяться. Злодій серед нас.",
        "text_ru": "Кто-то тайно берёт больше, чем положено. Пайки не сходятся. Вор среди нас.",
        "dc_min": 12, "dc_max": 18,
        "matchers": [],  # theft uses detective_matchers below
        "detective_matchers": [
            ("profession", ["детектив", "слідчий", "криміналіст", "слідователь"], 5),
            ("profession", ["поліцейськ", "юрист", "прокурор", "адвокат"], 3),
            ("profession", ["психолог"], 2),
            ("hobby",      ["розслідування", "дедукція", "шахи", "аналіз"], 2),
        ],
        "consequences": _C["theft"],
    },
    "equipment": {
        "name_uk": "🔧 Критична поломка",
        "name_ru": "🔧 Критическая поломка",
        "text_uk": "Система фільтрації повітря (або реактор / кріо-камера / навігація) дає збій. Є година до критичного рівня.",
        "text_ru": "Система фильтрации воздуха (или реактор / крио-камера / навигация) даёт сбой. Есть час до критического уровня.",
        "dc_min": 14, "dc_max": 20,
        "assigns_sick": False,
        "matchers": [
            ("profession", ["інженер", "ядерн", "космонавт", "астронавт", "атомник", "кібернетик"], 5),
            ("profession", ["механік", "програміст", "системний адмін"], 3),
            ("profession", ["електрик", "технік"], 2),
            ("hobby",      ["diy", "електроніка", "радіоаматор", "технічн"], 2),
            ("baggage",    ["набір інструментів", "планшет", "ноутбук", "спеціалізований"], 1),
        ],
        "consequences": _C["equipment"],
    },
}

# ─── Status info ──────────────────────────────────────────────────────────────

STATUS_EMOJI: dict[str, str] = {
    "sick":      "🤒",
    "immune":    "💊",
    "breakdown": "😤",
    "thief":     "🎭",
    "detective": "🔍",
    "repairing": "🛠️",
    "blackout":  "⚡",
    "skip_turn": "🚫",
}

# ─── Logic ────────────────────────────────────────────────────────────────────

def pick_event(catastrophe_text: str, recent_codes: list[str]) -> str | None:
    """Pick a random event code or None (no event this round).

    recent_codes: event codes that fired recently (cooldown list).
    """
    tag = detect_catastrophe_tag(catastrophe_text)
    base = EVENT_BASE_CHANCE.get(tag, 20)
    if random.randint(1, 100) > base:
        return None
    probs = EVENT_PROBS.get(tag, EVENT_PROBS["unknown"])
    available = {c: p for c, p in probs.items() if c not in recent_codes}
    if not available:
        available = probs
    total = sum(available.values())
    r = random.randint(1, total)
    cumulative = 0
    for code, prob in available.items():
        cumulative += prob
        if r <= cumulative:
            return code
    return list(available.keys())[-1]


def _match_card(matchers: list, card: dict) -> tuple[int, bool]:
    """Return (best_modifier_int, is_auto_success)."""
    best = 0
    for attr, keywords, mod in matchers:
        val = card.get(attr, "").lower()
        if any(k.lower() in val for k in keywords):
            if mod == "auto":
                return 0, True
            if isinstance(mod, int) and mod > best:
                best = mod
    return best, False


def find_executor(event_code: str, alive_players: list[dict]) -> tuple[dict | None, int, bool]:
    """Return (player, modifier, is_auto_success) for regular events.

    Returns (None, 0, False) if no one matches (auto_fail).
    """
    edef = EVENT_DEFINITIONS.get(event_code, {})
    matchers = edef.get("matchers", [])
    if not matchers:
        return None, 0, False
    best_player = None
    best_mod = -1
    for p in alive_players:
        card = json.loads(p.get("card_json") or "{}")
        mod, auto = _match_card(matchers, card)
        if auto:
            return p, 0, True
        if mod > best_mod:
            best_mod = mod
            best_player = p
    return best_player, max(best_mod, 0), False


def find_detective(alive_players: list[dict]) -> tuple[dict | None, int]:
    """Return (detective_player, modifier) for theft event."""
    edef = EVENT_DEFINITIONS["theft"]
    det_matchers = edef.get("detective_matchers", [])
    best_player = None
    best_mod = -1
    for p in alive_players:
        card = json.loads(p.get("card_json") or "{}")
        mod, auto = _match_card(det_matchers, card)
        eff_mod = 5 if auto else mod
        if eff_mod > best_mod:
            best_mod = eff_mod
            best_player = p
    return best_player, max(best_mod, 0)


def roll_d20() -> int:
    return random.randint(1, 20)


def resolve_roll(roll: int, modifier: int, dc: int, is_auto: bool, is_auto_fail: bool) -> str:
    """Return outcome code: auto_success|crit_success|success|fail|crit_fail|auto_fail."""
    if is_auto:
        return "auto_success"
    if is_auto_fail:
        return "auto_fail"
    if roll == 20:
        return "crit_success"
    if roll == 1:
        return "crit_fail"
    return "success" if (roll + modifier) >= dc else "fail"


def get_consequence(event_code: str, outcome: str, lang: str) -> str:
    edef = EVENT_DEFINITIONS.get(event_code, {})
    cons = edef.get("consequences", {})
    return cons.get(f"{outcome}_{lang}", cons.get(f"success_{lang}", ""))


def event_name(event_code: str, lang: str) -> str:
    edef = EVENT_DEFINITIONS.get(event_code, {})
    return edef.get(f"name_{lang}", event_code)


def event_text(event_code: str, lang: str) -> str:
    edef = EVENT_DEFINITIONS.get(event_code, {})
    return edef.get(f"text_{lang}", "")

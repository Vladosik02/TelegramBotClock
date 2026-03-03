# Скрипт первичного наполнения базы данных.
# Запуск: .venv/Scripts/python seed.py
import asyncio
from database.db import init_db, get_db


PS5_GAMES = [
    "FC 25",
    "Anno 1800",
    "It Takes Two",
    "Roblox",
    "UFC 5",
    "Fall Guys",
    "Five Nights at Freddy's",
    "Goat Simulator",
    "GTA V",
    "Human: Fall Flat",
    "Hollow Knight",
    "Mortal Kombat 1",
    "Poppy Playtime",
    "The Long Dark",
    "Need for Speed: Unbound",
    "Jurassic World Evolution",
]

PS4_GAMES = [
    "FC 25",
    "Asphalt Legends Unite",
    "Fall Guys",
    "A Way Out",
    "UFC 4",
    "GTA V",
    "It Takes Two",
    "Metro 2033 Redux",
    "Metro Exodus",
    "Mortal Kombat X",
    "Rocket League",
    "Unravel Two",
    "No Man's Sky",
]

# (назва, текст, локальний_файл_картинки)
# Кожне зображення містить 2 гри — одна картинка на двох
BOARD_GAMES = [
    (
        "Велоніmo",
        "Шалені велоперегони, де замість спортсменів — кумедні тварини!\n"
        "Блефуй, обганяй суперників і веди свою команду до перемоги.\n"
        "Ідеальна гра для сміху, азарту та веселого суперництва!\n\n"
        "Гравці: 2–5 | Час: 30–40 хв",
        "TableGame/5260682480984389072.jpg",
    ),
    (
        "Топ 10",
        "Вибуховий командний двіж, де смішні відповіді змагаються з ще смішнішими!\n"
        "Твоя задача — зрозуміти, хто на якому рівні абсурду.\n"
        "Грай, смійся та перевір, наскільки добре ви розумієте одне одного!\n\n"
        "Гравці: 4–9 | Час: 30 хв",
        "TableGame/5260682480984389072.jpg",
    ),
    (
        "Джуманджі",
        "Це не просто гра — це портал у світ пригод!\n"
        "Кидай кубики, вирішуй загадки й рятуйся від диких тварин.\n"
        "Тільки разом ви зможете вибратись з гри... або залишитесь назавжди!\n\n"
        "Гравці: 2–4 | Час: 15–40 хв",
        "TableGame/5260682480984389152.jpg",
    ),
    (
        "Тунель в Галактику",
        "Космічні перегони з перешкодами!\n"
        "Прокладай маршрут крізь зірки, уникай пасток і випереджай суперників у міжгалактичному тунелі.\n"
        "Стратегія, швидкість і трохи везіння — усе, що потрібно для перемоги!\n\n"
        "Гравці: 2–4 | Час: 45+ хв",
        "TableGame/5260682480984389152.jpg",
    ),
    (
        "Пандемія",
        "Кооперативна битва за людство!\n"
        "Разом із командою рятуй світ від спалаху смертельних вірусів.\n"
        "Плануй, ризикуй і перемагай... або програєте всі разом.\n"
        "Часу обмаль — гра починається прямо зараз!\n\n"
        "Гравці: 2–4 | Час: 45 хв",
        "TableGame/5262934280798076372.jpg",
    ),
    (
        "Париж: Місто вогнів",
        "Дуель краси та стратегії у вечірньому Парижі!\n"
        "Розміщуй плитки, підсвічуй пам'ятки і створи найяскравіше місто вогнів.\n"
        "Ідеальна гра для двох — інтелігентна, стильна та візуально захоплива.\n\n"
        "Гравці: 2 | Час: 30 хв",
        "TableGame/5262934280798076372.jpg",
    ),
    (
        "Цитаделі",
        "Гра блефу, стратегії та несподіваних перевтілень!\n"
        "Будуй місто, обирай ролі в секреті й перехитри суперників.\n"
        "Тут кожен хід — інтрига, а кожна партія — нова історія.\n"
        "Хто стане правителем?\n\n"
        "Гравці: 2–8 | Час: 30–60 хв",
        "TableGame/5262934280798076374.jpg",
    ),
    (
        "Вище суспільство",
        "Витончені аукціони для справжніх джентльменів і леді!\n"
        "Розкіш, статус, престиж — торгуйся, блефуй і не потрап у пастку марнотратства.\n"
        "Тільки найрозумніший з багатих стане переможцем!\n\n"
        "Гравці: 2–5 | Час: 15–30 хв",
        "TableGame/5262934280798076374.jpg",
    ),
    (
        "Рамен Рамен",
        "Весела кулінарна битва за найсмачнішу локшину!\n"
        "Збирай інгредієнти, створюй ідеальний рамен і випереджай суперників у цій апетитній сутичці.\n"
        "Проста, швидка й дуже смачна гра!\n\n"
        "Гравці: 1–4 | Час: 30 хв",
        "TableGame/5262934280798076439.jpg",
    ),
    (
        "Стежки Тукани",
        "Мандрівка кольоровими островами, де ти сам прокладаєш маршрут!\n"
        "З'єднуй пам'ятки, ринки й вулкани, отримуй бонуси й випереджай інших у пошуках ідеального шляху.\n"
        "Спокійна, але захоплива стратегія для всіх.\n\n"
        "Гравці: 1–8 | Час: 40–60 хв",
        "TableGame/5262934280798076439.jpg",
    ),
]


async def seed():
    await init_db()
    db = await get_db()

    # Clear existing games
    await db.execute("DELETE FROM ps_games")
    await db.execute("DELETE FROM board_game_instructions")
    await db.commit()

    # Insert PS5
    for title in PS5_GAMES:
        await db.execute(
            "INSERT INTO ps_games (platform, title) VALUES (?, ?)",
            ("PS5", title)
        )

    # Insert PS4
    for title in PS4_GAMES:
        await db.execute(
            "INSERT INTO ps_games (platform, title) VALUES (?, ?)",
            ("PS4", title)
        )

    # Insert board game instructions
    for game_name, text, image_path in BOARD_GAMES:
        await db.execute(
            "INSERT INTO board_game_instructions (game_name, content_type, text_content, local_image) VALUES (?, 'text', ?, ?)",
            (game_name, text, image_path)
        )

    await db.commit()

    ps5_count  = (await (await db.execute("SELECT COUNT(*) FROM ps_games WHERE platform='PS5'")).fetchone())[0]
    ps4_count  = (await (await db.execute("SELECT COUNT(*) FROM ps_games WHERE platform='PS4'")).fetchone())[0]
    instr_count = (await (await db.execute("SELECT COUNT(*) FROM board_game_instructions")).fetchone())[0]

    print("Done!")
    print(f"  PS5 games:    {ps5_count}")
    print(f"  PS4 games:    {ps4_count}")
    print(f"  Instructions: {instr_count}")


if __name__ == "__main__":
    asyncio.run(seed())

from aiogram.fsm.state import State, StatesGroup


class BookingForm(StatesGroup):
    zone           = State()   # Zone selection (inline keyboard)
    selecting_date = State()   # Calendar — waiting for date tap
    selecting_time = State()   # Time picker: start time only
    people         = State()   # Free text: number of people
    name           = State()   # Free text: contact name
    phone          = State()   # Free text: phone number
    payment        = State()   # Inline keyboard: payment type
    confirm        = State()   # Inline keyboard: confirm / cancel


class BirthdayForm(StatesGroup):
    selecting_date    = State()  # Calendar — waiting for date tap
    selecting_time    = State()  # Time picker: start
    selecting_time_end = State() # Time picker: end (only slots after start)
    entering_name     = State()  # Free text: name
    entering_age      = State()  # Free text: age (number)
    selecting_gender  = State()  # Inline keyboard: gender (conditional on age)
    entering_color    = State()  # Free text: favourite colour
    entering_phone    = State()  # Free text: phone number
    entering_wishes   = State()  # Free text: wishes
    selecting_payment = State()  # Inline keyboard: IBAN or cash


class SuggestionForm(StatesGroup):
    text = State()


# Admin content management forms
class AdminAddGame(StatesGroup):
    platform = State()
    title    = State()
    image    = State()


class AdminAddPhoto(StatesGroup):
    photo   = State()
    caption = State()


class AdminAddInstruction(StatesGroup):
    game_name = State()
    content   = State()


class AdminBroadcast(StatesGroup):
    typing  = State()   # waiting for message text
    confirm = State()   # waiting for confirm/cancel button


class AdminAddBooking(StatesGroup):
    zone    = State()
    date    = State()
    time    = State()
    name    = State()
    phone   = State()
    people  = State()
    payment = State()
    notes   = State()


class ProfileForm(StatesGroup):
    editing_name      = State()   # ввод нового имени
    editing_phone     = State()   # ввод нового телефона
    entering_ref_code = State()   # ввод реферального кода друга


class WalletForm(StatesGroup):
    entering_name   = State()  # ввод имени/фамилии для коментаря платежу
    entering_amount = State()  # ввод суммы пополнения


class BunkerHostForm(StatesGroup):
    selecting_count = State()   # host chooses max player count


class BunkerPlayerForm(StatesGroup):
    entering_code = State()     # player types session code

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Непрочитанные сообщения")],
        [KeyboardButton(text="Статистика")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    return keyboard


def get_unread_messages_keyboard(unread_chat_usernames: str) -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text=username)] for username in unread_chat_usernames]
    buttons.append([KeyboardButton(text="Меню")])
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    return keyboard


def get_answer_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Ответить")],
        [KeyboardButton(text="Меню")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    return keyboard


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Меню")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    return keyboard

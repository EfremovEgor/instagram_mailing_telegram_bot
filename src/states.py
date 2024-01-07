from aiogram.fsm.state import State, StatesGroup


class Navigation(StatesGroup):
    main_menu = State()
    unread_messages = State()
    reply_to_message = State()
    statistics = State()

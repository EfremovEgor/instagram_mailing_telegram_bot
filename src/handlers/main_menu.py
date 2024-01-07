from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
import pytz
from keyboards import (
    get_main_menu_keyboard,
    get_unread_messages_keyboard,
    get_answer_keyboard,
    get_cancel_keyboard,
)
from states import Navigation
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from models import NewMessage, MessageThread, Admin, MailingTarget, Worker
from sqlalchemy.future import select
from aiogram.utils.markdown import hbold
from aiogram.utils.formatting import as_key_value, as_marked_section, Bold, Text
import datetime

router = Router()


@router.message(Command("add_admin"))
async def get_admin(message: Message, session: AsyncSession):
    admins = await session.execute(
        select(Admin).where(Admin.admin_id == message.from_user.id)
    )
    if admins.first() is None:
        session.add(Admin(admin_id=message.from_user.id))
        await session.commit()
        await message.reply(
            f"{message.from_user.id} добавлен в качестве администратора"
        )
    else:
        await message.reply(f"{message.from_user.id} уже существует как администратор")


@router.message(Command("Меню"))
@router.message(F.text == "Меню")
@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.set_state(Navigation.main_menu)
    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Navigation.main_menu, F.text == "Статистика")
async def unread_messages_chosen(message: Message, session: AsyncSession):
    query = await session.execute(select(Worker).with_only_columns(Worker.name))
    workers = query.scalars().all()
    statistics = list()
    current_datetime = datetime.datetime.now(pytz.utc)

    for worker in workers:
        data = dict()
        query = await session.execute(
            select(MailingTarget).where(
                MailingTarget.status == "DONE",
                MailingTarget.worker == worker,
            )
        )
        targets = query.scalars().all()
        data["name"] = worker
        data["sent_in_a_week"] = sum(
            (current_datetime - target.done_at).days <= 7 for target in targets
        )
        data["sent_in_a_day"] = sum(
            (current_datetime - target.done_at).days <= 1 for target in targets
        )
        data["was_replied_by_target_day"] = sum(
            (current_datetime - target.done_at).days <= 1
            and target.was_answered_by_target
            for target in targets
        )
        statistics.append(data)
    query = await session.execute(
        select(MailingTarget).where(
            MailingTarget.status == "DONE",
        )
    )
    targets = query.scalars().all()
    global_statistics = dict()
    global_statistics["sent_all_time"] = len(targets)
    global_statistics["sent_in_a_week"] = sum(
        (current_datetime - target.done_at).days <= 7 for target in targets
    )
    global_statistics["sent_in_a_day"] = sum(
        (current_datetime - target.done_at).days <= 1 for target in targets
    )
    content = Text(
        as_marked_section(
            Bold(f"\nОбщая статистика"),
            as_marked_section(
                Bold("Отправлено за все время: "),
                global_statistics["sent_all_time"],
                marker="  ",
            ),
            as_marked_section(
                Bold("Всего отправлено за неделю: "),
                global_statistics["sent_in_a_week"],
                marker="  ",
            ),
            as_marked_section(
                Bold("Всего отправлено за день: "),
                global_statistics["sent_in_a_day"],
                marker="  ",
            ),
            as_marked_section(
                Bold("Ответили за день: "),
                data["was_replied_by_target_day"],
                marker="  ",
            ),
        ),
        *[
            as_marked_section(
                Bold(f"\nСтатистика по боту '{data['name']}'"),
                as_marked_section(
                    Bold("Отправлено за неделю: "), data["sent_in_a_week"], marker="  "
                ),
                as_marked_section(
                    Bold("Отправлено за день: "), data["sent_in_a_day"], marker="  "
                ),
                as_marked_section(
                    Bold("Ответили за день: "),
                    data["was_replied_by_target_day"],
                    marker="  ",
                ),
            )
            for data in statistics
        ],
    )
    await message.answer(**content.as_kwargs(), reply_markup=get_main_menu_keyboard())


@router.message(Navigation.main_menu, F.text == "Непрочитанные сообщения")
async def unread_messages_chosen(
    message: Message, state: FSMContext, session: AsyncSession
):
    query = await session.execute(
        select(NewMessage).where(NewMessage.status == "PENDING")
    )
    await state.set_state(Navigation.unread_messages)
    unread_messages = query.scalars().all()
    await message.answer(
        "Выберите чат:",
        reply_markup=get_unread_messages_keyboard(
            unread_message.sender_username for unread_message in unread_messages
        ),
    )


@router.message(Navigation.unread_messages, F.text == "Ответить")
async def reply_message_chosen(
    message: Message, state: FSMContext, session: AsyncSession
):
    await state.set_state(Navigation.reply_to_message)
    await session.commit()
    await message.answer("Введите сообщение:", reply_markup=get_cancel_keyboard())


@router.message(Navigation.reply_to_message)
async def reply_message_chosen(
    message: Message, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    unread_message_instance = await session.get(NewMessage, data["unread_message_id"])
    unread_message_instance.answer = message.text
    unread_message_instance.status = "ANSWERED"
    await session.commit()

    await state.set_state(Navigation.main_menu)
    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Navigation.unread_messages)
async def chat_chosen(message: Message, state: FSMContext, session: AsyncSession):
    query = await session.execute(
        select(NewMessage).where(NewMessage.sender_username == message.text)
    )

    selected_unread_message = query.scalars().first()

    query = await session.execute(
        select(MessageThread).where(
            MessageThread.thread_username == selected_unread_message.sender_username,
            MessageThread.worker == selected_unread_message.worker,
        )
    )
    message_thread: list[MessageThread] = query.scalars().all()
    content = Text(
        as_marked_section(
            Bold(f"Выбран чат {message.text})"),
            *[
                as_marked_section(
                    Bold(message_.sender_username), message_.message, marker="  "
                )
                for message_ in message_thread
            ],
        )
    )
    await state.update_data(
        worker=selected_unread_message.worker,
        unread_message_id=selected_unread_message.id,
    )

    await message.answer(
        **content.as_kwargs(),
        reply_markup=get_answer_keyboard(),
    )

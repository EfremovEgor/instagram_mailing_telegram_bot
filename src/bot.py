from aiogram import Bot, Dispatcher
import config
from database import get_session, async_session_generator
from middleware.database import DbSessionMiddleware
import models
import asyncio
from handlers import (
    main_menu,
)
from sqlalchemy import update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram.filters import Command
from aiogram.types import Message

bot = Bot(token=config.TOKEN, parse_mode="HTML")

# bot = Bot(token=config.TOKEN)
# dp = Dispatcher(bot)


# @dp.message_handler(commands="send_notifications")
# async def cmd_test1(message: types.Message):
#     await notify_admins_of_unread_messages()


async def notify_admins_of_unread_messages():
    async with get_session() as session:
        query = await session.execute(select(models.Admin))

        admins = query.scalars().all()
        query = await session.execute(
            select(models.NewMessage).where(models.NewMessage.notified == False)
        )
        unnotified_messages: list[models.NewMessage] = query.scalars().all()

    tasks = []
    for unnotified_message in unnotified_messages:
        try:
            for admin in admins:
                tasks.append(
                    asyncio.create_task(
                        bot.send_message(
                            admin.admin_id,
                            f"На ваше сообщение в чате с {unnotified_message.sender_username} ответили: '{unnotified_message.message}' ",
                        )
                    )
                )
            message_instance = await session.get(
                models.NewMessage, unnotified_message.id
            )
            message_instance.notified = True
            await session.commit()
        except Exception as ex:
            print(ex)
    await asyncio.gather(*tasks)


def schedule_tasks():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        notify_admins_of_unread_messages,
        trigger="interval",
        seconds=60,
        max_instances=1,
    )

    scheduler.start()


async def main() -> None:
    schedule_tasks()
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session_generator()))
    dp.callback_query.middleware(CallbackAnswerMiddleware())
    dp.include_routers(
        main_menu.router,
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

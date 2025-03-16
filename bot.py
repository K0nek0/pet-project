import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from handler import router
from kb import get_subscription_keyboard
from database import Database, DatabaseMiddleware
import asyncio

logging.basicConfig(level=logging.INFO)

async def check_subscriptions(bot: Bot, db: Database):
    while True:
        soon_expired = await db.get_soon_expired_subscriptions()
        for user in soon_expired:
            end_date = user['subscription_end'].strftime("%d.%m.%Y")
            await bot.send_message(
                user['user_id'],
                f"⚠️ Ваша подписка истекает {end_date}!"
            )

        expired = await db.get_expired_subscriptions()
        for user in expired:
                await db.unsubscribe_user(user['user_id'])
                await bot.send_message(
                    user['user_id'],
                    "❌ Ваша подписка истекла!",
                    reply_markup=get_subscription_keyboard(False)
                )

        await asyncio.sleep(3600)

async def main():
    db = Database()
    await db.create_pool()
    await db.init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DatabaseMiddleware(db))
    dp.include_router(router)

    asyncio.create_task(check_subscriptions(bot, db))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

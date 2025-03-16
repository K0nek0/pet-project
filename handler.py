from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database import Database
from datetime import datetime
from kb import get_subscription_keyboard, get_confirmation_keyboard
from utils import UnsubscribeStates, timedelta_to_dhm

router = Router()

@router.message(Command("start"))
async def process_start(message: Message, db: Database):
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username
    )
    status = await db.get_subscription_status(message.from_user.id)
    await message.answer(
        "Привет! Я бот для подписки на новости.\n"
        "Используйте кнопки ниже для управления подпиской.",
        reply_markup=get_subscription_keyboard(status["subscribe"])
    )


@router.message(F.text == "Подписаться", StateFilter(None))
async def process_subscribe(message: Message, db: Database):
    status = await db.get_subscription_status(message.from_user.id)
    
    if status["subscribe"] is True:
        await message.answer("❌ У вас уже есть активная подписка!")
        return
    
    await db.subscribe_user(message.from_user.id)
    await message.answer(
        "✅ Вы успешно подписались на 1 месяц!",
        reply_markup=get_subscription_keyboard(True)
    )


@router.message(F.text == "Отписаться")
async def process_unsubscribe(message: Message, db: Database, state: FSMContext):
    status = await db.get_subscription_status(message.from_user.id)
    
    if status["subscribe"] is False:
        await message.answer("❌ Подписка неактивна")
        return
    
    await message.answer(
        "Вы уверены, что хотите отписаться?",
        reply_markup=get_confirmation_keyboard()
    )
    await state.set_state(UnsubscribeStates.waiting_for_confirmation)

@router.message(
    F.text.in_(["Да", "Нет"]),
    UnsubscribeStates.waiting_for_confirmation
)
async def process_unsubscribe_confirmation(message: Message, db: Database, state: FSMContext):
    if message.text == "Да":
        await db.unsubscribe_user(message.from_user.id)
        await message.answer(
            "❌ Вы отписались от обновлений.",
            reply_markup=get_subscription_keyboard(False)
        )
    else:
        await message.answer(
            "Отписка отменена.",
            reply_markup=get_subscription_keyboard(True)
        )
    
    await state.clear()


@router.message(F.text == "Статус", StateFilter(None))
async def process_status(message: Message, db: Database):
    status = await db.get_subscription_status(message.from_user.id)
    
    if status["subscribe"] is False:
        await message.answer("❌ Подписка неактивна")
        return
    
    end_date = status["subscription_end"].strftime("%d.%m.%Y")
    days_left = (status["subscription_end"] - datetime.now())
    days, hours, minutes = timedelta_to_dhm(days_left)
    
    if days >= 1:
        await message.answer(
            f"✅ Ваша подписка активна до {end_date}\n"
            f"Осталось дней: {days}"
        )
    elif hours >= 1:
        await message.answer(
            f"✅ Ваша подписка скоро кончится!\n"
            f"Осталось часов: {hours}"
        )
    else:
        await message.answer(
            f"✅ Ваша подписка скоро кончится!\n"
            f"Осталось минут: {minutes}"
        )

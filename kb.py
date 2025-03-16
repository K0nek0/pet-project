from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def create_keyboard(buttons: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in buttons],
        resize_keyboard=True
    )

def get_subscription_keyboard(is_subscribed: bool) -> ReplyKeyboardMarkup:
    return create_keyboard(
        [["Статус", "Отписаться"]] if is_subscribed else [["Подписаться"]]
    )

def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    return create_keyboard([["Да", "Нет"]])

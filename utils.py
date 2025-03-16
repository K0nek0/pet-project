from aiogram.fsm.state import State, StatesGroup

class UnsubscribeStates(StatesGroup):
    waiting_for_confirmation = State()


def timedelta_to_dhm(duration):
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    # seconds = (seconds % 60)
    return days, hours, minutes

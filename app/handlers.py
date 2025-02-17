## реализована отписка в тг канал

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.generators import gpt

import time
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

router = Router()

# ID телеграм-канала, куда будут отправляться сообщения
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1002387101531')) # тут канал бунта стоит

# Список исключений по chat.id
EXCLUDED_USER_IDS = [1062594217, 987654321]  # Замените на реальные ID пользователей


# Определяем состояния
class Generate(StatesGroup):
    text = State()
    previous_question = State()
    previous_response = State()


# Создаем кнопку для связи
def create_contact_keyboard():
    write_button = InlineKeyboardButton(text="Связаться сейчас!", url="https://t.me/Caporest")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[write_button]])
    return keyboard


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    print(message.chat.id)
    print(message.chat.username)

    # Логируем событие старта бота
    with open('start.txt', 'a', encoding='utf-8') as f:
        timestamp = time.time()
        value = datetime.datetime.fromtimestamp(timestamp)
        f.write(f'\n Старт бота|{value.strftime("%Y-%m-%d %H:%M:%S")}|{message.chat.id}|{message.chat.username}')

    # Отправляем приветственное сообщение и очищаем состояние
    await message.answer(
        "Здравствуйте! Я ассистент косметологии 'BuntClinic' \n \nМожете задать любой интересующий Вас вопрос)"
    )
    await state.clear()


@router.message(F.text)
async def generate(message: Message, state: FSMContext):
    # Проверка предыдущего контекста (состояния) пользователя
    previous_question = await state.get_data()

    # Запоминаем текущее сообщение пользователя
    await state.update_data(previous_question=message.text)

    # Передаем и прошлый контекст, и текущее сообщение в GPT для анализа
    if previous_question:
        prompt = f"Пользователь спросил: {previous_question['previous_question']}\nВы ответили: {previous_question['previous_response']}\n\nТеперь пользователь спрашивает: {message.text}"
    else:
        prompt = message.text

    # Отправляем запрос в GPT с учетом контекста
    response = await gpt(prompt)

    # Сохраняем ответ от бота
    await state.update_data(previous_response=response.choices[0].message.content)

    # Логируем запрос пользователя и отправляем ответ
    with open('rar.txt', 'a', encoding='utf-8') as f:
        timestamp = time.time()
        value = datetime.datetime.fromtimestamp(timestamp)
        f.write(
            f'\nЗапрос|{value.strftime("%Y-%m-%d %H:%M:%S")}|{message.chat.id}|{message.chat.username}|{message.text}'
        )

    await message.answer(
        response.choices[0].message.content,
        reply_markup=create_contact_keyboard()
    )

    # Отправляем сообщение в канал, если пользователь не в списке исключений
    if message.chat.id not in EXCLUDED_USER_IDS:
        channel_message = (
            f"💬 *Новое сообщение от пользователя:*\n\n"
            f"👤 Пользователь: @{message.chat.username} \n"
            f"📩 Сообщение: {message.text}"
        )
        await message.bot.send_message(CHANNEL_ID, channel_message, parse_mode='Markdown')

    await state.set_state(Generate.text)
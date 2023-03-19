import asyncio
import logging
from aiogram import Bot, Dispatcher, types, executor
import motor.motor_asyncio
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage


logging.basicConfig(level=logging.INFO)
bot = Bot(token=")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
cluster = motor.motor_asyncio.AsyncIOMotorClient("")
collection = cluster.chat.articles


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    try:
        user_data = {
            'user_id': message.from_user.id,
            'user_name': message.from_user.full_name
        }
        collection.chat.telegram_users.insert_one(user_data)
        await message.reply("Вас приветствует ассистент нашего корпоративного портала! Я буду присылать вам важные сообщения и свежие новости, относящиеся к жизни компании")
    except:
        pass


@dp.message_handler(commands=['allnews'])
async def cmd_news(message: types.Message):
    if message.from_user.id == 745457912:
        try:
            articles = await collection.find().to_list(None)
            await bot.send_message(chat_id=message.from_user.id, text='Последние 10 новостей:')
            for article in articles:
                await bot.send_message(chat_id=message.from_user.id, text=article['title'])
            await bot.send_message(message.from_user.id, '✅Успешная рассылка✅')
        except:
            pass


@dp.message_handler(commands=['deletenews'])
async def cmd_news(message: types.Message):
    if message.from_user.id == 745457912:
        try:
            filter = {'title': f'{message.text[12:]}'} 
            result = await collection.delete_one(filter)
            await bot.send_message(message.from_user.id, '✅Успешно удалено✅')
        except:
            pass


@dp.message_handler(commands=['news'])
async def cmd_news(message: types.Message):
    if message.from_user.id == 745457912:
        try:
            article = await collection.find_one(sort=[('$natural', -1)], limit=1)
            text = f'{article["title"]} \n{article["content"]}'
            users = await collection.chat.telegram_users.find().to_list(None)
            for user in users:
                await bot.send_message(chat_id=user['user_id'], text=text)
            await bot.send_message(message.from_user.id, '✅Рассылка прошла успешно✅')
        except:
            pass


@dp.message_handler(commands=['sendall'])
async def cmd_sendall(message: types.Message):
    if message.from_user.id == 745457912:
        try:
            text = message.text[9:]
            users = await collection.chat.telegram_users.find().to_list(None)
            for user in users:
                await bot.send_message(chat_id=user['user_id'], text=text)
            await bot.send_message(message.from_user.id, '✅Рассылка прошла успешно✅')
        except:
            pass

class StatesList:
    name = "Name state"
    age = "Age state"


class FSMRegistration(StatesGroup):
    name = State()
    age = State()


@dp.message_handler(commands="articleadd")
async def cmd_start(message: types.Message):
    if message.from_user.id == 745457912:
        await message.answer("Отправь название новости")
        await FSMRegistration.name.set()


@dp.message_handler(state=FSMRegistration.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Отправь описание статьи")
    await FSMRegistration.age.set()


@dp.message_handler(state=FSMRegistration.age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    user_data = await state.get_data()
    article_data = {
        'title': user_data['name'],
        'content': user_data['age'],
        'author': message.from_user.id,
    }
    collection.insert_one(article_data)
    await bot.send_message(message.from_user.id, '✅Запись добавлена✅')
    await state.finish()


async def on_startup(dp):
    await bot.send_message(chat_id='YOUR_CHAT_ID', text='Бот запущен')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(on_startup(dp))
    executor.start_polling(dp, skip_updates=True)
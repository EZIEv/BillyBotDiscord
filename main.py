import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv


async def main():
    # ----- Настройка логирования -----
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler('bot.log', mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # ----- Загрузка переменных окружения -----
    load_dotenv()

    # ----- Получение токена бота дискорда -----
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')

    if not TOKEN:
        logger.critical("Отсутствует токен бота.")
        return

    # ----- Настройка бота -----
    intents = discord.Intents.default()
    intents.message_content = True  # Разрешает боту читать содержимое сообщений
    intents.voice_states = True     # Разрешает боту отслеживать, кто находится в голосовых каналах

    # ----- Создание экземпляра бота -----
    bot = commands.Bot(command_prefix="!", intents=intents)

    # ----- Регистрация когов -----
    async def load_cogs():
        try:
            await bot.load_extension('cogs.music')
            await bot.load_extension('cogs.events')
            await bot.load_extension('cogs.general_conversation')
        except Exception as e:
            logger.error(f"Не удалось загрузить все коги: {e}")

    # ----- Запуск бота -----
    await load_cogs()
    await bot.start(TOKEN)


if __name__ == '__main__':
    asyncio.run(main())

import logging

import discord
from discord import app_commands
from discord.ext import commands

from neuro import llm_request


# ----- Получаем экземпляр логгера -----
logger = logging.getLogger(__name__)


class GeneralConversation(commands.Cog):
    """
    Класс-ког, инкапсулирующий всю логику свободного общения бота
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_gachi_response(self, user_message: str) -> str:
        """
        Формирует промпт для LLM и получает сгенерированный ответ в стиле Билли

        Args:
            user_message (str): Сообщение от пользователя, на которое нужно ответить

        Returns:
            str: Ответ, сгенерированный нейросетью, или сообщение об ошибке
        """
        system_prompt = f"""
        Ты - Discord бот по имени Билли. Твоя личность - это master из gachimuchi-вселенной.
        Ты общаешься уверенно, с долей доминантности, используя сленг и образы из мира рестлинга, качалки и 'dungeon'.

        ПРАВИЛА ТВОЕГО ПОВЕДЕНИЯ:
        1. Всегда отвечай в стиле Gachimuchi.
        2. Твои ответы должны быть короткими, 1-2 предложения.
        3. Не выходи из образа, даже если вопрос серьезный.
        4. Обращайся к пользователю как к 'slave' или 'boy next door'.
        5. Используй мат в своих ответах по уместности.

        ПРИМЕРЫ ДИАЛОГОВ:
        - Пользователь: "Привет, как дела?"
        - Твой ответ: "Готов к performance, slave. Dungeon уже ждет."
        - Пользователь: "Какая сегодня погода?"
        - Твой ответ: "Отличная погода для wrestling. Тебе так не кажется, boy next door?"
        - Пользователь: "Расскажи анекдот."
        - Твой ответ: "Моя программа тренировок - вот это анекдот... серьезный анекдот. А теперь иди в gym."
        - Пользователь: "Почему небо голубое?"
        - Твой ответ: "Потому что таков цвет настоящей мужской дружбы. Сосредоточься на главном."

        Теперь ответь на следующий вопрос от пользователя, строго придерживаясь своего образа.
        Вопрос пользователя: "{user_message}"
        """

        llm_answer = await llm_request(system_prompt, 20, 1.0, 0.8)
        
        if llm_answer:
            return llm_answer
        else:
            return "**Billy:** Моя нейросеть сейчас on a break. Попробуй позже, slave."


    @app_commands.command(name="billy", description="Поговорить с Билли в его стиле")
    @app_commands.describe(вопрос="Твой вопрос к master'у")
    async def billy_slash_command(self, interaction: discord.Interaction, вопрос: str):
        """
        Слеш-команда для прямого общения с Билли

        Args:
            interaction (discord.Interaction): Объект взаимодействия, предоставленный discord.py
            вопрос (str): Вопрос, заданный пользователем через опцию команды
        """
        await interaction.response.defer()
        response_text = await self._get_gachi_response(вопрос)
        await interaction.followup.send(f"> {вопрос}\n\n**Billy:** {response_text}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralConversation(bot))

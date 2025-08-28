import asyncio
import logging

from discord.ext import commands

from executor import execute_command
from handler import _handle_neurobilly


# ----- Получаем экземпляр логгера -----
logger = logging.getLogger(__name__)


class Events(commands.Cog):
    """
    Класс-ког, который объединяет все основные обработчики событий
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.disconnect_timers = {} # {guild_id: asyncio.Task}


    @commands.Cog.listener()
    async def on_ready(self):
        """
        Событие, которое выполняется один раз, когда бот успешно залогинился и готов к работе
        """
        try:
            synced = await self.bot.tree.sync()
            logger.info(f"Синхронизировано {len(synced)} команд.")
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")

        logger.info(f'Master {self.bot.user} готов ебать!')


    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Основной обработчик сообщений. Выполняется каждый раз, когда в чате появляется новое сообщение
        Анализирует сообщение на наличие одного из префиксов и запускает соответствующую логику
        """
        # Игнорируем сообщения от других ботов (включая самого себя) и личные сообщения
        if message.author.bot or not message.guild:
            return
        
        # Определение префиксов и маршрутизация
        raw_content = message.content.strip()
        prefix = "билли "               # Для обычных команд
        neuro_prefix = "нейробилли "    # Для команд, требующих анализа нейросетью
        convo_prefix = "билли поясни "  # Для общения с нейросетью

        # Свободное общение
        if raw_content.lower().startswith(convo_prefix):
            user_question = raw_content[len(convo_prefix):].strip()
            if not user_question:
                return await message.channel.send("**Billy:** за что пояснить, slave?")
            
            convo_cog = self.bot.get_cog("GeneralConversation")

            thinking_msg = await message.channel.send("Billy обдумывает твой вопрос...")
            response = await convo_cog._get_gachi_response(user_question)
            await thinking_msg.edit(content=f"> {user_question}\n\n**Billy:** {response}")

            return

        # Команды через нейросеть
        if raw_content.lower().startswith(neuro_prefix):
            user_request = raw_content[len(neuro_prefix):].strip()
            if not user_request:
                return await message.channel.send("**Billy:** чего ты хочешь, slave? Сформулируй мысль")

            thinking_message = await message.channel.send("Billy обдумывает твой вопрос...")
            
            model_command = await _handle_neurobilly(user_request)
            
            await thinking_message.edit(content=f"Billy решил, что ты хочешь: `{model_command}`. Выполняю...")
            await execute_command(self.bot, message, model_command)
            return

        # Обычные команды
        if raw_content.lower().startswith(prefix):
            command = raw_content[len(prefix):].strip()
            await execute_command(self.bot, message, command)
            return
        
    
    async def auto_disconnect(self, guild):
        """Задача, которая ждет 60 секунд и отключает бота, если канал все еще пуст"""
        await asyncio.sleep(60)
        # Повторно проверяем, что бот все еще в канале и что он пуст.
        if guild.voice_client and len([m for m in guild.voice_client.channel.members if not m.bot]) == 0:
            logger.info(f"Отключаюсь от сервера '{guild.name}', так как канал пуст.")
            music_cog = self.bot.get_cog('Music')
            if music_cog:
                await music_cog._leave(guild)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Обработчик событий в голосовых каналах. Используется для автоматического выхода бота
        Срабатывает, когда пользователь подключается, отключается, мьютится и т.д.
        """
        voice_client = member.guild.voice_client
        # Проверяем, что бот вообще находится в голосовом канале
        if not voice_client or not voice_client.channel: 
            return
        
        guild_id = member.guild.id

        # Пользователь зашел в канал, где сидит одинокий бот
        if after.channel == voice_client.channel and before.channel != voice_client.channel:
            # Если для этого сервера есть активный таймер на отключение, отменяем его
            if guild_id in self.disconnect_timers:
                logger.info(f"Пользователь '{member.name}' зашел. Отменяю таймер отключения для '{member.guild.name}'.")
                self.disconnect_timers[guild_id].cancel()
                del self.disconnect_timers[guild_id]

        # Пользователь вышел из канала, оставив бота одного
        elif before.channel == voice_client.channel and after.channel != voice_client.channel:
            if len([m for m in voice_client.channel.members if not m.bot]) == 0:
                # Если уже есть таймер, отменяем его на всякий случай (хотя этого не должно происходить).
                if guild_id in self.disconnect_timers:
                    self.disconnect_timers[guild_id].cancel()
                
                logger.info(f"Канал на сервере '{member.guild.name}' опустел. Запускаю 60-секундный таймер на отключение.")
                # Создаем и сохраняем новую задачу таймера.
                self.disconnect_timers[guild_id] = self.bot.loop.create_task(self.auto_disconnect(member.guild))


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))

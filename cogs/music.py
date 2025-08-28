import logging

import discord
from discord import app_commands
from discord.ext import commands

from YTDLSource import YTDLSource

# ----- Получаем экземпляр логгера -----
logger = logging.getLogger(__name__)


class Music(commands.Cog):
    """
    Класс-ког, инкапсулирующий всю музыкальную функциональность бота
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.music_queues = {}  # {guild_id: [queue]}
        self.text_channels = {} # {guild_id: channel_id}


    def get_queue(self, guild_id: int):
        """
        Безопасно получает очередь для указанного сервера

        Если для сервера еще не существует очереди, метод создает пустой список
        и возвращает его. Это избавляет от необходимости проверок на существование ключа.

        Args:
            guild_id (int): ID сервера

        Returns:
            list: Очередь воспроизведения для данного сервера
        """
        return self.music_queues.setdefault(guild_id, [])


    async def play_next(self, guild: discord.Guild):
        """
        Основной "движок" воспроизведения. Берет следующий трек из очереди и запускает его
        Эта функция вызывается рекурсивно через коллбэк `after` в `voice_client.play`

        Args:
            guild (discord.Guild): Сервер, на котором нужно воспроизвести следующий трек
        """
        queue = self.get_queue(guild.id)
        if not queue:
            return

        # Берем первый трек из очереди и одновременно удаляем его
        query = queue.pop(0)
        text_channel = self.bot.get_channel(self.text_channels.get(guild.id))

        try:
            player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)

            # Запускаем воспроизведение
            guild.voice_client.play(player, after=lambda e: self.bot.loop.create_task(self.play_next(guild)))
            if text_channel:
                await text_channel.send(f"**Billy:** сейчас мы долбим: **{player.title}**")
        except Exception as e:
            logger.error(f"Ошибка воспроизведения: {e}")
            if text_channel:
                await text_channel.send("**Billy:** меня накрыло, попускаю трек")
            # Пытаемся запустить следующий трек, даже если текущий не удался
            await self.play_next(guild)


    # ----- Внутренние методы -----

    async def _play(self, text_channel: discord.TextChannel, voice_channel: discord.VoiceChannel, query: str) -> str:
        """Внутренний метод для добавления трека в очередь и начала воспроизведения"""
        guild = text_channel.guild
        # Подсоединяем бота к голосовому каналу, если еще нет
        if not guild.voice_client:
            await voice_channel.connect()
        
        # Добавляем трек в очередь
        queue = self.get_queue(guild.id)
        queue.append(query)
        self.text_channels[guild.id] = text_channel.id

        if not guild.voice_client.is_playing():
            await self.play_next(guild)
            return f"**Billy:** слушай **{query}** пока не оглохнешь"
        else:
            return f"**Billy:** я запомнил тебя, всех твоих родственников и этот трек тоже: **{query}**"


    def _skip(self, guild: discord.Guild) -> str:
        """Внутренний метод для пропуска текущего трека"""
        if guild.voice_client and guild.voice_client.is_playing():
            guild.voice_client.stop()   # Остановка плеера вызовет коллбэк и запустит play_next.
            return "**Billy:** трек попущен"
        return "**Billy:** нечего попускать, иди сам попустись"


    def _pause(self, guild: discord.Guild) -> str:
        """Внутренний метод для постановки на паузу"""
        if guild.voice_client and guild.voice_client.is_playing():
            guild.voice_client.pause()
            return "**Billy:** я тебя выебал так красиво, мой slave"
        return "**Billy:** я бы развлекся, но сейчас ничего не играет"


    def _resume(self, guild: discord.Guild) -> str:
        """Внутренний метод для возобновления воспроизведения"""
        if guild.voice_client and guild.voice_client.is_paused():
            guild.voice_client.resume()
            return "**Billy:** ебемся дальше"
        return "**Billy:** в уши не долбись, трек играет"


    def _stop(self, guild: discord.Guild) -> str:
        """Внутренний метод для полной остановки и очистки очереди"""
        if guild.voice_client:
            self.get_queue(guild.id).clear()
            guild.voice_client.stop()
            return "**Billy:** в следующий раз я хочу больше твоего cum, fucking slave"
        return "**Billy:** мои яички пусты, дорогой"


    async def _leave(self, guild: discord.Guild) -> str:
        """Внутренний метод для отключения от голосового канала"""
        if guild.voice_client:
            self.music_queues.pop(guild.id, None)
            await guild.voice_client.disconnect()
            return "**Billy:** ляяя ты чорт"
        return "**Billy:** пошел наухй долбоеб, я не в канале"


    def _queue(self, guild: discord.Guild) -> str:
        """Внутренний метод для отображения очереди. Возвращает Embed или строку"""
        queue = self.get_queue(guild.id)
        if not queue:
            return "**Billy:** мои яички пусты"
        
        queue_list = "\n".join([f"{i+1}. `{track}`" for i, track in enumerate(queue)])
        embed = discord.Embed(title="Будем слушать следующее", description=queue_list, color=discord.Color.blue())
        return embed


    def _clear(self, guild: discord.Guild) -> str:
        """Внутренний метод для очистки очереди без остановки плеера"""
        queue = self.get_queue(guild.id)
        if not queue:
            return "**Billy:** мои яички и так были пусты"
            
        queue.clear() 
        return "**Billy:** Ааааа, кончил. Мои яички опустошены"


    def _remove(self, guild: discord.Guild, number: int):
        """Внутренний метод для удаления трека из очереди по номеру"""
        queue = self.get_queue(guild.id)
        
        if not (1 <= number <= len(queue)):
            return "**Billy:** Ты еблан? Нет такого номера"
        
        removed_track = queue.pop(number - 1)
        return f"**Billy:** я вырвал из списка: `{removed_track}`."


    # ----- Слеш-команды -----

    @app_commands.command(name="play", description="Воспроизвести музыку по названию или ссылке")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("**Billy:** Ты глухой, slave, как ты можешь слышать", ephemeral=True)
        await interaction.response.defer()
        message = await self._play(interaction.channel, interaction.user.voice.channel, query)
        await interaction.followup.send(message)


    @app_commands.command(name="skip", description="Пропустить текущий трек")
    async def skip(self, interaction: discord.Interaction):
        message = await self._skip(interaction.guild)
        await interaction.response.send_message(message, ephemeral=True)


    @app_commands.command(name="pause", description="Поставить на паузу")
    async def pause(self, interaction: discord.Interaction):
        message = await self._pause(interaction.guild)
        await interaction.response.send_message(message, ephemeral=True)


    @app_commands.command(name="resume", description="Возобновить воспроизведение")
    async def resume(self, interaction: discord.Interaction):
        message = await self._resume(interaction.guild)
        await interaction.response.send_message(message, ephemeral=True)


    @app_commands.command(name="stop", description="Остановить и очистить очередь")
    async def stop(self, interaction: discord.Interaction):
        message = await self._stop(interaction.guild)
        await interaction.response.send_message(message)


    @app_commands.command(name="leave", description="Отключить бота от голосового канала")
    async def leave(self, interaction: discord.Interaction):
        message = await self._leave(interaction.guild)
        await interaction.response.send_message(message)


    @app_commands.command(name="queue", description="Показать очередь")
    async def queue(self, interaction: discord.Interaction):
        result = self._queue(interaction.guild)
        if isinstance(result, discord.Embed):
            await interaction.response.send_message(embed=result)
        else:
            await interaction.response.send_message(result, ephemeral=True)


    @app_commands.command(name="clear", description="Очистить очередь")
    async def clear(self, interaction: discord.Interaction):
        message = self._clear(interaction.guild)
        await interaction.response.send_message(message)


    @app_commands.command(name="remove", description="Удалить трек из очереди")
    @app_commands.describe(номер="Номер трека, который нужно удалить")
    async def remove(self, interaction: discord.Interaction, номер: int):
        message = self._remove(interaction.guild, номер)
        await interaction.response.send_message(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))

import asyncio

import discord
from discord.ext import commands


async def execute_command(bot: commands.bot, message: discord.Message, command: str):
    """
    Асинхронная функция, которая анализирует и выполняет текстовую команду

    Args:
        bot (commands.Bot): Экземпляр текущего бота, необходим для получения доступа к когам
        message (discord.Message): Объект сообщения, содержащий контекст (канал, автор, сервер)
        command (str): "Чистая" строка команды, уже без префикса ("билли" или "нейробилли")
    """
    # Получаем экземпляр когов
    music_cog = bot.get_cog('Music')
    if not music_cog:
        return


    # ----- Команды с аргументами -----

    # Команда "поставь", выполняет поиск трека
    if command.startswith("поставь "):
        # Проверяем, находится ли автор сообщения в голосовом канале.
        if not message.author.voice:
            return await message.channel.send("Ты глухой, епта")

        query = command[7:].strip()
        if not query.lower().startswith(("http://", "https://")):
            if query.lower().endswith("заебал"): 
                query = query[:-6].strip()
            else:
                query = f"гачи {query}"

        response = await music_cog._play(message.channel, message.author.voice.channel, query)
        await message.channel.send(response)
    
    # Команда "убери" убирает трек по номеру
    elif command.startswith("убери "):
        parts = command.split()
        if len(parts) < 2:
            return await message.channel.send("**Billy:** укажи номер трека, boy.")
        try:
            track_number = int(parts[1])
            response = music_cog._remove(message.guild, track_number)
            await message.channel.send(response)
        except ValueError:
            await message.channel.send("**Billy:** это не похоже на номер, boy.")


    # ----- Команды без аргументов -----

    else:
        # Использование словаря (карты команд)
        command_map = {
            "очередь": music_cog._queue,
            "пропусти": music_cog._skip,
            "пауза": music_cog._pause,
            "продолжи": music_cog._resume,
            "стоп": music_cog._stop,
            "очищай нахуй": music_cog._clear,
            "ты ошибся дверью друг": music_cog._leave
        }

        if command in command_map:
            func = command_map[command]

            # Некоторые методы асинхронные (`async def`) и требуют `await`,
            # а некоторые - обычные (`def`)
            if asyncio.iscoroutinefunction(func):
                response = await func(message.guild)
            else: 
                response = func(message.guild)
            
            # проверка метод _queue возвращает объект Embed,
            # который нужно отправлять особым образом
            if isinstance(response, discord.Embed): 
                await message.channel.send(embed=response)
            else: 
                await message.channel.send(response)

        
        # ----- Обработка нераспознанных запросов -----

        # Если нейросеть не смогла распознать команду
        elif command == "unknown_command":
            await message.channel.send("**Billy:** я тебя не понял, slave. Попробуй перефразировать.")
        # Если при обращении к API произошла ошибка
        elif command.startswith("error:"):
            await message.channel.send(f"**Billy:** моя нейросеть сейчас on a break: {command}")
        # Если команда не подошла ни под одно из условий выше
        else:
            await message.channel.send("**Billy:** ты вообще ебнутый? Нет такой команды.")

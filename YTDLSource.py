import asyncio
import os

import discord
import yt_dlp


# ----- Получение пути куки для ютуба -----
COOKIE_PATH = os.getenv('COOKIE_PATH')

# ----- Настройка yt_dlp -----
ytdl_format_options = {
    'format': 'bestaudio/best',                              # Выбирать аудиодорожку наилучшего качества
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',     # Шаблон для имен скачиваемых файлов (если stream=False)
    'restrictfilenames': True,                               # Ограничить имена файлов только ASCII символами, чтобы избежать проблем с ОС
    'noplaylist': True,                                      # Если дана ссылка на плейлист, скачивать только одно видео, а не весь плейлист
    'nocheckcertificate': True,                              # Не проверять SSL сертификаты (иногда помогает обойти проблемы с соединением)
    'ignoreerrors': False,                                   # Не игнорировать ошибки (если видео недоступно, лучше сразу получить ошибку)
    'logtostderr': False,                                    # Не выводить логи yt-dlp в консоль
    'quiet': True,                                           # Максимально "тихий" режим, минимум вывода в консоль
    'age_limit': 99,                                         # Устанавливает фиктивный возраст для обхода возрастных ограничений
    'cookiefile': COOKIE_PATH,                               # Путь к файлу с cookies для аутентификации
    'no_warnings': True,                                     # Отключить предупреждения от yt-dlp
    'default_search': 'auto',                                # Если передан не URL, а просто текст, yt-dlp будет искать его (например, на YouTube)
    'source_address': '0.0.0.0'                              # Принудительно использовать IPv4, что может решить проблемы с подключением в некоторых сетях
}

# ----- Настройка ffmpeg -----
ffmpeg_options = {
    'options': '-vn'  # Опция для проигрывания аудио без видео компонента
}

# ----- Создание экземпляра yt_dlp -----
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    """
    Представляет собой аудио-источник для discord.py, совместимый с yt-dlp
    """
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')


    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        """
        Асинхронный фабричный метод для создания экземпляра YTDLSource из URL или поискового запроса

        Args:
            url (str): URL видео/аудио или поисковый запрос
            loop (asyncio.AbstractEventLoop, optional): Цикл событий asyncio. Если None, будет получен текущий
            stream (bool, optional): Если True, аудио будет проигрываться напрямую по URL
                                     не скачиваясь на диск. Это быстрее, но ссылка может "протухнуть"
                                     Если False, файл будет сначала скачан.

        Returns:
            YTDLSource: Экземпляр этого класса, готовый к воспроизведению
        """
        # Получаем текущий цикл событий, если он не был передан
        loop = loop or asyncio.get_event_loop()

        # Извлекаем данные о видео/аудио в отдельном потоке
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        # Если это плейлист, выбираем первый элемент
        if 'entries' in data:
            data = data['entries'][0]
        
        # Если streaming включён, используем прямую ссылку на аудио
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

import aiohttp
import asyncio
import logging
import os


# ----- Получаем экземпляр логгера -----
logger = logging.getLogger(__name__)


async def llm_request(prompt: str, max_retries: int, initial_delay: float, temperature: float) -> str:
    """
    Отправляет запрос к LLM через OpenRouter API с встроенной логикой повторных попыток

    Args:
        prompt (str): Полностью сформированный системный промпт для нейросети
        max_retries (int): Максимальное количество попыток отправки запроса в случае сбоя
        initial_delay (float): Начальная задержка в секундах перед первой повторной попыткой
        temperature (float): Параметр "температуры" для модели. Низкие значения (близко к 0)
                             делают ответы более предсказуемыми, высокие (близко к 1) - более креативными

    Returns:
        str: Ответ от модели в виде строки, или пустая строка (`""`), если все попытки провалились
    """
    # Получаем API ключ из переменных окружения
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not API_KEY:
        logger.critical("Отсутствует токен OpenRouter API.")

    # Указываем конкретную модель, которую будем использовать
    MODEL_NAME = "google/gemini-2.0-flash-exp:free"

    for attempt in range(max_retries):
        try:
            # Устанавливаем общий таймаут для запроса в 15 секунд, чтобы бот не "зависал" надолго
            timeout = aiohttp.ClientTimeout(total=15.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    # Формируем тело JSON-запроса в соответствии с документацией OpenAI/OpenRouter
                    json={
                        "model": MODEL_NAME,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature
                        }
                ) as response:
                    if 200 <= response.status < 300:
                        data = await response.json()
                        return data['choices'][0]['message']['content'].strip()
                    
                    error_text = await response.text()
                    logger.warning(f"Попытка {attempt + 1} общения не удалась. Статус: {response.status}. Ответ: {error_text}")

        # Ловим ошибки сети (например, нет интернета) или ошибки таймаута
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Попытка {attempt + 1} общения не удалась. Ошибка сети: {e}")
        
        # Если это была не последняя попытка, ждем перед следующей
        if attempt < max_retries - 1:
            # Вычисляем задержку по принципу экспоненциальной выдержки (1с, 2с, 4с...)
            delay = initial_delay * (2 ** attempt)
            await asyncio.sleep(delay)

    logger.error("Все попытки обращения к LLM провалились.")
    return ""

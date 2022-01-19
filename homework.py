import time
import logging
import telegram
import requests
import os
from dotenv import load_dotenv


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправка результатов пользователю."""
    try:
        logger.info('Сообщение отправлено!')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as e:
        logger.error(f'Сообщение не отправлено: {e}.')


def get_api_answer(current_timestamp):
    """Запрос API Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        logger.error("API Яндекс.Практикума не отвечает!")
        raise AttributeError("API Яндекс.Практикума не отвечает!")
    return response.json()


def check_response(response):
    """Проверка ответа."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        logger.error('Ключ homeworks не найден!')
        raise KeyError('Ключ homeworks не найден!')
    if not isinstance(homeworks, list):
        logger.error("Некорректный формат списка работ!")
        raise TypeError("Неправильно указан тип для homeworks")
    if len(homeworks) == 0:
        logger.info("Список работ пуст.")
    return homeworks


def parse_status(homework):
    """Извлечение статусов."""
    try:
        homework_name = homework['homework_name']
    except KeyError:
        logger.error('Ключ homework_name не найден!')
        raise KeyError('Ключ homework_name не найден!')
    try:
        homework_status = homework['status']
    except KeyError:
        logger.error('Ключ status не найден!')
        raise KeyError('Ключ status не найден!')
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}"-{verdict}'
    raise AttributeError(f'Статус {homework_status} не найден.')


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if token is None:
            logger.critical('Отстутствует токен!')
            return False
        return True


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = check_response(get_api_answer(current_timestamp))
            for homework in response:
                send_message(bot, parse_status(homework))
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

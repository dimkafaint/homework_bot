import time
import logging
from urllib import response
import telegram
import requests
import os
from dotenv import load_dotenv
from telegram.ext import CommandHandler, Updater

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


def send_message(bot, message):
    '''Отправка результатов пользователю'''
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Запрос API Практикума"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise AttributeError("API Яндекс.Практикума не отвечает!")
    return response.json()


def check_response(response):
    homeworks = response.get("homeworks")
    if type(homeworks) is not list:
        logger.error("Некорректный формат списка работ!")
    if not homeworks:
        raise AssertionError("Список работ пуст.")
    return homeworks


def parse_status(homework):
    homework_name = response.get("homework_name")
    homework_status = response.get('homework_status')
    if homework_name or homework_status is None:
        raise AttributeError('Ключ не найден.')
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}"-{verdict}'
    raise AttributeError(f'Статус {homework_status} не найден.')


def check_tokens():
    """Проверка доступности переменных окружения"""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if token is None:
            logger.critical(f'Отстутствует токен! Проверь .env!')
            return False
        return True


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            if check_response(response):
                send_message(bot, parse_status(response))
                current_timestamp = int(time.time())
                time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
            time.sleep(RETRY_TIME)
        else:
            pass
        # updater.start_polling()
        # updater.idle()
    


if __name__ == '__main__':
    main()

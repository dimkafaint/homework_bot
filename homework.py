import logging
import os
import requests
import time

from dotenv import load_dotenv
from http.client import HTTPException
from json import JSONDecodeError
import telegram


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
SERVER_ERROR = "Неверный статус сервера. {0}, Headers{1}, Params{2}"
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def send_message(bot, message):
    """Отправка результатов пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as e:
        logger.exception(f'Сообщение не отправлено: {e}.')
    else:
        logger.info(f'Сообщение {message} отправлено!')


def get_api_answer(current_timestamp):
    """Запрос API Практикума."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=params,
                                timeout=10)
    except requests.Timeout as e:
        logger.exception(f'Нет ответа от сервера. {e}')
    if response.status_code != 200:
        raise HTTPException(SERVER_ERROR.format(
            response.status_code, HEADERS, params))
    try:
        return response.json()
    except JSONDecodeError:
        logger.exception('Неподдерживаемый формат.')


def check_response(response):
    """Проверка ответа."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        raise KeyError('Ключ homeworks не найден!')
    if not isinstance(homeworks, list):
        raise TypeError("Неправильно указан тип для homeworks")
    if not homeworks:
        logger.info("Список работ пуст.")
    return homeworks


def parse_status(homework):
    """Извлечение статуса."""
    homework_name = homework['homework_name']
    status = homework['status']
    verdict = HOMEWORK_VERDICTS[status]
    if status in HOMEWORK_VERDICTS:
        return f'Изменился статус проверки работы "{homework_name}"-{verdict}'
    raise KeyError(f'Статус {status} не найден.')


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    tokens_status = True
    for token in tokens:
        if tokens[token] is None:
            logger.error(f'Нет токена {token}.')
            tokens_status = False
    return tokens_status


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.error("Запуск программы невозможен.")
        quit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = parse_status(homeworks[0])
                if homework is not None:
                    send_message(bot, homework)
                    current_timestamp = response.get(
                        'current_date', current_timestamp)
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            send_message(bot, f'Ошибка {error}')
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        filename=__file__ + '.log',
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        level=logging.INFO)
    main()

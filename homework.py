import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TOKENS = {
    'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
    'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
}
RETRY_TIME = 600
TIMEOUT = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
SERVER_ERROR = "Ошибка сервера. {0}, URL{1},Headers{2}, Params{3}, Timeout{4}"
MSG_SUCCESS = 'Сообщение {0} отправлено!'
MSG_FAIL = 'Сообщение {0} не отправлено: {1}.'
RESPONSE_KEY_FAIL = 'Ключ homeworks не найден!'
RESPONSE_TYPE_FAIL = "Неправильный тип для homeworks. Тип - {0}"
EMPTY_LIST = "Список работ пуст."
JSON_ERROR = "Отказ от обслуживания. {0}, {1}"
VERDICT = 'Изменился статус проверки работы "{0}"-{1}'
STATUS_FAIL = 'Статус {0} не найден.'
MISSING_TOKEN = 'Нет токена: {0}.'
CHECK_TOKENS_ERROR = "Запуск программы невозможен."
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def send_message(bot, message):
    """Отправка результатов пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(MSG_SUCCESS.format(message))
    except telegram.TelegramError as e:
        logger.exception(MSG_FAIL.format(message, e))


def get_api_answer(current_timestamp):
    """Запрос API Практикума."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=params,
                                timeout=TIMEOUT)
    except requests.RequestException as e:
        raise ConnectionError(SERVER_ERROR.format(
            e, ENDPOINT, HEADERS, params, TIMEOUT))
    if response.status_code != requests.codes.ok:
        raise ConnectionError(SERVER_ERROR.format(
            response.status_code, ENDPOINT, HEADERS, params, TIMEOUT))
    if 'code' and 'error' in response.json():
        raise ConnectionError(JSON_ERROR.format(
            response.json()['code'], response.json()['error']))
    return response.json()


def check_response(response):
    """Проверка ответа."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        raise KeyError(RESPONSE_KEY_FAIL)
    if not isinstance(homeworks, list):
        raise TypeError(RESPONSE_TYPE_FAIL.format(type(homeworks)))
    if not homeworks:
        logger.info(EMPTY_LIST)
    return homeworks


def parse_status(homework):
    """Извлечение статуса."""
    homework_name = homework['homework_name']
    status = homework['status']
    if status in VERDICTS:
        verdict = VERDICTS[status]
        return VERDICT.format(homework_name, verdict)
    raise ValueError(STATUS_FAIL.format(status))


def check_tokens():
    """Проверка доступности переменных окружения."""
    token_status = True
    lost_tokens = [token for token in TOKENS if globals()[token] is None]
    if lost_tokens:
        for i in lost_tokens:
            logger.error(MISSING_TOKEN.format(i))
            token_status = False
    return token_status


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise RuntimeError(CHECK_TOKENS_ERROR)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework_verdict = parse_status(homeworks[0])
                if homework_verdict is not None:
                    send_message(bot, homework_verdict)
            current_timestamp = response.get(
                'current_date', current_timestamp)
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            send_message(bot, f'Сбой в работе программы: {error}')
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        filename=__file__ + '.log',
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        level=logging.INFO)
    main()

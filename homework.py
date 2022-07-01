import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (RequestsErrorException, SendingErrorException,
                        StatusCodeErrorException)

load_dotenv()

logger = logging.getLogger()
fileHandler = logging.FileHandler("logfile.log")
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s %(lineno)d %(funcName)s'
)
streamHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICT_NAME = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram чат, определяемый переменной окружения.
    TELEGRAM_CHAT_ID. Принимает на вход два параметра: экземпляр класса Bot и
    строку с текстом сообщения.
    """
    try:
        logger.info('Начата отправка сообщения в телеграм')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception:
        raise SendingErrorException('Ошибка отправки сообщения в телеграм')
    else:
        logger.info('Сообщение в телеграм отправлено')


def get_api_answer(current_timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса. В качестве параметра.
    функция получает временную метку. В случае успешного запроса должна
    вернуть ответ API, преобразовав его из формата JSON к типам данных Python.
    """
    try:
        params = {'from_date': current_timestamp}
        logger.info(f'Делаем запрос на {ENDPOINT}')
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params=params)
        print(f'{ENDPOINT}{HEADERS}{params}')
    except Exception as error:
        raise RequestsErrorException(f'Ошибка при запросе к API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise StatusCodeErrorException(f'Ошибка {ENDPOINT}{HEADERS}{params}')
    return response.json()


def check_response(response):
    """
    Проверяет ответ API на корректность. В качестве параметра функция получает.
    ответ API, приведенный к типам данных Python. Если ответ API соответствует
    ожиданиям, то функция должна вернуть список домашних работ (он может быть
    и пустым), доступный в ответе API по ключу 'homeworks'.
    """
    logger.info('Старт проверки ответа сервера')
    if not isinstance(response, dict):
        raise TypeError(
            'Ответ API отличен от словаря')
    if 'homeworks' not in response:
        raise KeyError('В словаре response нет ключа "homeworks"')
    if 'current_date' not in response:
        raise KeyError('В словаре response нет ключа "current_date"')
    if not isinstance(response['homeworks'], list):
        raise TypeError("Ответ API: homework не список")
    if len(response['homeworks'][0]) == 0:
        raise KeyError('Ответ API: список пуст')
    return response['homeworks'][0]


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы. В.
    качестве параметра функция получает только один элемент из списка домашних
    работ. В случае успеха, функция возвращает подготовленную для отправки в
    Telegram строку, содержащую один из вердиктов словаря HOMEWORK_STATUSES.
    """
    if 'homework_name' not in homework:
        raise KeyError('Произошла ошибка "homework_name"')
    if 'status' not in homework:
        raise KeyError('Произошла ошибка "status"')

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in VERDICT_NAME:
        logger.error(f'Статус {homework_status} не найден')
        raise KeyError(f'Статус {homework_status} не найден')

    verdict = VERDICT_NAME[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """
    Проверяет доступность переменных окружения, которые необходимы для.
    работы программы. Если отсутствует хотя бы одна переменная
    окружения — функция должна вернуть False, иначе — True.
    """
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(
            'Отсутствуют одна или несколько переменных окружения'
        )
        sys.exit(1)
    current_timestamp = int(time.time())
    last_status = ''
    error_cache_message = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            message = parse_status(check_response(response))
            if message != last_status:
                send_message(bot, message)
                last_status = message
            current_timestamp = response.get('current_date', current_timestamp)
        except Exception as error:
            logging.error("Произошло исключение", exc_info=True)
            error_message = f'Сбой в работе программы: {error}'
            if error_message != error_cache_message:
                send_message(bot, error_message)
                error_cache_message = error_message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger()
fileHandler = logging.FileHandler("logfile.log")
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
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


HOMEWORK_STATUSES = {
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
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение отправлено')
    except Exception:
        logger.error('Ошибка отправки сообщения в телеграм')
        raise Exception('Ошибка отправки сообщения в телеграм')


def get_api_answer(current_timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса. В качестве параметра.
    функция получает временную метку. В случае успешного запроса должна
    вернуть ответ API, преобразовав его из формата JSON к типам данных Python.
    """
    try:
        timestamp = current_timestamp or int(time.time())
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params=params)
        if response.status_code != HTTPStatus.OK:
            raise Exception('HTTPStatus NOT FOUND')
        return response.json()
    except Exception as error:
        logger.error(f'Ошибка при запросе к API: {error}')
        raise Exception(f'Ошибка при запросе к API: {error}')


def check_response(response):
    """
    Проверяет ответ API на корректность. В качестве параметра функция получает.
    ответ API, приведенный к типам данных Python. Если ответ API соответствует
    ожиданиям, то функция должна вернуть список домашних работ (он может быть
    и пустым), доступный в ответе API по ключу 'homeworks'.
    """
    homework = response['homeworks'][0]
    return homework


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы. В.
    качестве параметра функция получает только один элемент из списка домашних
    работ. В случае успеха, функция возвращает подготовленную для отправки в
    Telegram строку, содержащую один из вердиктов словаря HOMEWORK_STATUSES.
    """
    last_homework = homework
    if 'homework_name' not in last_homework:
        raise KeyError('Произошла ошибка "homework_name"')
    if 'status' not in last_homework:
        raise KeyError('Произошла ошибка "status"')

    homework_name = last_homework['homework_name']
    homework_status = last_homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        logger.error(f'Статус {homework_status} не найден')
        raise KeyError

    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """
    Проверяет доступность переменных окружения, которые необходимы для.
    работы программы. Если отсутствует хотя бы одна переменная
    окружения — функция должна вернуть False, иначе — True.
    """
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = ''
    error_cache_message = ''
    if not check_tokens():
        logger.critical(
            'Отсутствуют одна или несколько переменных окружения'
        )
        raise Exception(
            'Отсутствуют одна или несколько переменных окружения'
        )
    while True:
        try:
            response = get_api_answer(current_timestamp)
            message = parse_status(check_response(response))
            if message != status:
                send_message(bot, message)
                status = message
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            logger.error(error)
            message2 = f'Сбой в работе программы: {error}'
            if message2 != error_cache_message:
                send_message(bot, message2)
                error_cache_message = message2
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

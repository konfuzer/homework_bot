import logging
import os
import sys
import time

import requests
import telebot
from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import APIRequestError, MissingKeyError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def check_tokens():
    """Проверка наличия всех необходимых переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    missing_tokens = [name for name, token in tokens.items() if not token]
    if missing_tokens:
        return False
    return True


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    logger.info(f'Начало отправки сообщения: "{message}"')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Бот отправил сообщение: "{message}"')
        return True
    except (telebot.apihelper.ApiException,
            requests.RequestException) as error:
        logger.error(f'Ошибка при отправке сообщения: {error}')
        return False


def get_api_answer(timestamp):
    """Запрос к API Практикум Домашка."""
    params = {'from_date': timestamp}
    logger.info(f'Начало запроса к API: {ENDPOINT}, заголовки:'
                f'{HEADERS}, параметры: {params}')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.RequestException as error:
        raise APIRequestError(f'Ошибка при запросе к API: {error}')

    if response.status_code != HTTPStatus.OK:
        raise APIRequestError(f'Ошибка при запросе к Практикум:'
                              f'API вернул статус {response.status_code}')

    return response.json()


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError(f'Ответ API должен быть словарём, получен тип:'
                        f'{type(response)}')
    if 'homeworks' not in response or 'current_date' not in response:
        raise MissingKeyError('В ответе API отсутствуют необходимые ключи.')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Тип данных домашек в ответе API должен быть список.')
    return response['homeworks']


def parse_status(homework):
    """Извлекает статус домашней работы и возвращает сообщение."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_name is None or homework_status is None:
        raise KeyError('Отсутствуют ожидаемые ключи в ответе API')

    verdicts = HOMEWORK_VERDICTS

    verdict = verdicts.get(homework_status)

    if verdict is None:
        raise ValueError(
            f'Неизвестный статус домашней работы: {homework_status}')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствует обязательная переменная окружения!')
        sys.exit()

    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error_message = None

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if send_message(bot, message):
                    timestamp = response.get('current_date', timestamp)
                    last_error_message = None
            else:
                logger.debug('Новых статусов нет.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if last_error_message != message:
                send_message(bot, message)
                last_error_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    main()

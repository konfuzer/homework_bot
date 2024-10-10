class HomeworkBotError(Exception):
    """Базовое исключение для бота."""


class APIRequestError(HomeworkBotError):
    """Исключение при ошибках запроса к API."""


class MissingKeyError(HomeworkBotError):
    """Исключение при отсутствии нужных ключей в ответе API."""


class UnknownStatusError(HomeworkBotError):
    """Исключение для неизвестного статуса работы."""

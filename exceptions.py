class HomeworkBotError(Exception):
    """Базовое исключение для бота."""
    pass


class APIRequestError(HomeworkBotError):
    """Исключение при ошибках запроса к API."""
    pass


class MissingKeyError(HomeworkBotError):
    """Исключение при отсутствии нужных ключей в ответе API."""
    pass


class UnknownStatusError(HomeworkBotError):
    """Исключение для неизвестного статуса работы."""
    pass

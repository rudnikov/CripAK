class CryptoError(Exception):
    """Базовое исключение крипто-модуля."""

class WrongPasswordError(CryptoError):
    """Неверный пароль или повреждённые данные."""

class CryptoError(Exception):
    """Базовое исключение крипто-модуля."""


class WrongPasswordError(CryptoError):
    """Неверный пароль или повреждённые данные."""
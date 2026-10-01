from pathlib import Path
from typing import Optional, Callable

from crypt_app.core.crypto import encrypt_bytes, decrypt_bytes


def encrypt_file(src: Path, dst: Path, password: str, progress_cb: Optional[Callable[[int], None]] = None) -> None:
    """
    Шифрует файл src и записывает результат в dst.

    :param src: Путь к исходному файлу (не изменяется)
    :param dst: Путь к выходному файлу (будет создан/перезаписан)
    :param password: Пароль для шифрования
    :param progress_cb: Необязательный колбэк прогресса (0–100).
                        Вызывается с 100 после завершения.
    :raises FileNotFoundError: если src не существует или dst в несуществующей папке
    :raises PermissionError: если нет прав на чтение/запись
    """
    blob_file = src.read_bytes()
    encoding_blob_file = encrypt_bytes(blob_file, password)
    dst.write_bytes(encoding_blob_file)

    if progress_cb is not None:
        progress_cb(100)


def decrypt_file(src: Path, dst: Path, password: str, progress_cb: Optional[Callable[[int], None]] = None) -> None:
    """
    Расшифровывает файл src и записывает результат в dst.

    :param src: Путь к зашифрованному файлу
    :param dst: Путь к выходному файлу (будет создан/перезаписан)
    :param password: Пароль для расшифровки
    :param progress_cb: Необязательный колбэк прогресса (0–100)
    :raises FileNotFoundError: если src не существует
    :raises WrongPasswordError: если пароль неверный или данные повреждены
    :raises PermissionError: если нет прав на чтение/запись
    """
    blob_encoding_file = src.read_bytes()
    decoding_blob_file = decrypt_bytes(blob_encoding_file, password)
    dst.write_bytes(decoding_blob_file)

    if progress_cb is not None:
        progress_cb(100)

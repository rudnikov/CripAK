from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os

from crypt_app.core.exceptions import CryptoError, WrongPasswordError
from crypt_app import config


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=config.KEY_SIZE,
        salt=salt,
        iterations=config.ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def _validate_blob(blob: bytes) -> None:
    if len(blob) < config.HEADER_SIZE:
        raise CryptoError("Данные слишком короткие")


def encrypt_bytes(data: bytes, password: str) -> bytes:
    """
    Шифрует байты с использованием AES-256-GCM.

    Формат результата:
        [salt (16 байт)] [nonce (12 байт)] [ciphertext + tag]

    :param data: Произвольные байты для шифрования
    :param password: Пароль пользователя
    :return: Зашифрованный blob
    """

    salt = os.urandom(config.SALT_SIZE)
    nonce = os.urandom(config.NONCE_SIZE)
    key = _derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, data, None)
    return salt + nonce + ciphertext


def decrypt_bytes(blob: bytes, password: str) -> bytes:
    """Расшифровывает blob. Кидает WrongPasswordError при неверном пароле."""

    _validate_blob(blob)

    salt = blob[:config.SALT_SIZE]
    nonce = blob[config.SALT_SIZE:config.SALT_SIZE + config.NONCE_SIZE]
    ciphertext = blob[config.SALT_SIZE + config.NONCE_SIZE:]
    key = _derive_key(password, salt)

    try:
        return AESGCM(key).decrypt(nonce, ciphertext, None)
    except InvalidTag as e:
        raise WrongPasswordError("Неверный пароль или повреждённые данные") from e

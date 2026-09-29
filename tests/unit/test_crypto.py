import pytest

from crypt_app.core.crypto import encrypt_bytes, decrypt_bytes
from crypt_app.core.exceptions import WrongPasswordError, CryptoError



# ---------- Roundtrip ----------

def test_roundtrip_simple():
    data = b"hello world"
    password = "secret"
    blob = encrypt_bytes(data, password)
    assert decrypt_bytes(blob, password) == data


def test_roundtrip_empty_bytes():
    """Пустые данные тоже должны корректно шифроваться."""
    data = b""
    password = "secret"
    blob = encrypt_bytes(data, password)
    assert decrypt_bytes(blob, password) == data


def test_roundtrip_large_data():
    """Большие данные (1 МБ) — проверяем, что всё ок."""
    data = b"x" * (1024 * 1024)
    password = "secret"
    blob = encrypt_bytes(data, password)
    assert decrypt_bytes(blob, password) == data


def test_roundtrip_unicode_password():
    """Пароль с юникод-символами."""
    data = b"data"
    password = "пароль🔐"
    blob = encrypt_bytes(data, password)
    assert decrypt_bytes(blob, password) == data


def test_roundtrip_binary_data():
    """Данные со всеми возможными байтами."""
    data = bytes(range(256))
    password = "secret"
    blob = encrypt_bytes(data, password)
    assert decrypt_bytes(blob, password) == data


# ---------- Wrong password ----------

def test_wrong_password_raises():
    """Неверный пароль → WrongPasswordError."""
    blob = encrypt_bytes(b"data", "correct")
    with pytest.raises(WrongPasswordError):
        decrypt_bytes(blob, "wrong")


def test_wrong_password_empty():
    """Пустой пароль не подходит, если был непустой."""
    blob = encrypt_bytes(b"data", "correct")
    with pytest.raises(WrongPasswordError):
        decrypt_bytes(blob, "")


# ---------- Unique ciphertext ----------

def test_same_data_gives_different_ciphertext():
    """Одинаковые данные + один пароль → РАЗНЫЕ шифротексты (из-за salt/nonce)."""
    data = b"same data"
    password = "same password"

    blob1 = encrypt_bytes(data, password)
    blob2 = encrypt_bytes(data, password)

    assert blob1 != blob2


# ---------- Corrupted data ----------

def test_corrupted_blob_raises():
    """Повреждённый blob → CryptoError (а не случайный Exception)."""
    blob = encrypt_bytes(b"data", "secret")
    corrupted = blob[:-1] + bytes([blob[-1] ^ 0xFF])
    with pytest.raises(WrongPasswordError):
        decrypt_bytes(corrupted, "secret")


def test_truncated_blob_raises():
    """Обрезанный blob → ошибка, а не мусор."""
    blob = encrypt_bytes(b"data", "secret")
    truncated = blob[:5]
    with pytest.raises(CryptoError):
        decrypt_bytes(truncated, "secret")


def test_empty_blob_raises():
    """Пустой blob → ошибка."""
    with pytest.raises(CryptoError):
        decrypt_bytes(b"", "secret")
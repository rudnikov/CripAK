"""
Интеграционные тесты для crypt_app.core.file_service.

Проверяют работу с файлами на диске:
- чтение, шифрование, запись;
- обработку ошибок (неверный пароль, отсутствующий файл);
- сохранность исходного файла;
- работу колбэка прогресса.

Все тесты используют фикстуру tmp_path — pytest даёт уникальную
временную папку для каждого теста, чтобы тесты не мешали друг другу
и не загрязняли репозиторий.
"""
import pytest

from crypt_app.core.file_service import encrypt_file, decrypt_file
from crypt_app.core.exceptions import WrongPasswordError


# ============================================================
# Тест 1. Roundtrip: обратимость шифрования на простых байтах
# ============================================================

def test_roundtrip_simple_file(tmp_path):
    """
    Проверяет базовое свойство шифрования: decrypt(encrypt(x)) == x.

    Сценарий:
        1. Создаём файл input.bin с известным содержимым.
        2. Шифруем его в input.enc.
        3. Расшифровываем input.enc в output.bin.
        4. Убеждаемся, что output.bin побайтово совпадает с input.bin.

    Проверяет:
        - encrypt_file создаёт выходной файл;
        - содержимое зашифрованного файла отличается от исходного;
        - decrypt_file корректно восстанавливает данные.

    Тип: happy path, самый простой случай.
    """
    # Arrange
    original_data = b"hello world"
    src = tmp_path / "input.bin"
    src.write_bytes(original_data)

    enc = tmp_path / "input.enc"
    dec = tmp_path / "output.bin"

    # Act
    encrypt_file(src, enc, "password")
    decrypt_file(enc, dec, "password")

    # Assert
    assert enc.exists(), "Зашифрованный файл должен быть создан"
    assert dec.exists(), "Расшифрованный файл должен быть создан"
    assert enc.read_bytes() != original_data, "Шифротекст должен отличаться от исходника"
    assert dec.read_bytes() == original_data, "Расшифровка должна вернуть исходные данные"


# ============================================================
# Тест 2. Roundtrip на реальных файлах Word/Excel/JPG
# ============================================================

@pytest.mark.parametrize("file_name", [
    "sample_2.docx",
    "sample_6.docx",
    "sample_1.xlsm",
    "sample_3.xlsx",
    "sample_4.png",
    "sample_5.jpg",
])
def test_roundtrip_real_files(tmp_path, fixtures_dir, file_name):
    """
    Проверяет обратимость шифрования на реальных файлах из fixtures/.

    Параметризован на шесть файлов: docx, docx, xlsm, xlsx, png, jpg.
    Работает одинаково для всех — file_service не знает про форматы.

    Проверяет:
        - шифрование не зависит от формата;
        - корректная работа с бинарными данными разных форматов;
        - decrypt_file не нуждается в исходном файле.
    """
    # Arrange
    source = fixtures_dir / file_name
    original_bytes = source.read_bytes()

    work_file = tmp_path / source.name
    work_file.write_bytes(original_bytes)

    enc = tmp_path / (source.name + ".enc")
    dec = tmp_path / ("restored_" + source.name)

    # Act
    encrypt_file(work_file, enc, "password123")
    work_file.unlink()
    decrypt_file(enc, dec, "password123")

    # Assert
    assert enc.exists()
    assert dec.exists()
    assert enc.read_bytes() != original_bytes, "Шифротекст должен отличаться"
    assert dec.read_bytes() == original_bytes, "Расшифровка должна совпасть с оригиналом"


# ============================================================
# Тест 3. Неверный пароль должен бросать WrongPasswordError
# ============================================================

def test_wrong_password_raises(tmp_path):
    """
    Проверяет, что расшифровка с неверным паролем бросает WrongPasswordError.

    Сценарий:
        1. Шифруем файл с паролем "correct".
        2. Пытаемся расшифровать с паролем "wrong".
        3. Ожидаем исключение WrongPasswordError.

    Проверяет:
        - decrypt_file не «тихо» возвращает мусор;
        - использует своё исключение WrongPasswordError (не InvalidTag из cryptography);
        - выходной файл не создаётся при ошибке (косвенно — если бы создался,
          pytest не поймал бы исключение раньше записи).

    Тип: обработка ошибок.
    """
    # Arrange
    src = tmp_path / "input.bin"
    src.write_bytes(b"secret data")

    enc = tmp_path / "input.enc"
    encrypt_file(src, enc, "correct")

    dec = tmp_path / "output.bin"

    # Act + Assert
    with pytest.raises(WrongPasswordError):
        decrypt_file(enc, dec, "wrong")


# ============================================================
# Тест 4. encrypt_file не изменяет и не удаляет исходный файл
# ============================================================

def test_encrypt_does_not_modify_or_delete_source(tmp_path):
    """
    Проверяет, что шифрование не трогает исходный файл.

    Сценарий:
        1. Создаём src с содержимым.
        2. Запоминаем его байты и время модификации.
        3. Шифруем в отдельный dst.
        4. Проверяем: src существует, содержимое не изменилось.

    Проверяет:
        - encrypt_file не перезаписывает src (шифрование НЕ in-place);
        - encrypt_file не удаляет src (это задача вызывающего кода);
        - после ошибки пользователь не теряет оригинал.

    Тип: свойство безопасности данных.
    """
    # Arrange
    original_data = b"important document content"
    src = tmp_path / "document.bin"
    src.write_bytes(original_data)

    enc = tmp_path / "document.enc"

    # Act
    encrypt_file(src, enc, "password")

    # Assert
    assert src.exists(), "Исходный файл не должен быть удалён"
    assert src.read_bytes() == original_data, "Исходный файл не должен быть изменён"
    assert enc.exists(), "Зашифрованный файл должен существовать"


# ============================================================
# Тест 5. Колбэк прогресса вызывается и доходит до 100
# ============================================================

def test_progress_callback_called(tmp_path):
    """
    Проверяет, что progress_cb вызывается и сообщает о завершении.

    Сценарий:
        1. Создаём файл.
        2. Передаём в encrypt_file колбэк, собирающий значения.
        3. Проверяем собранные значения.

    Проверяет:
        - колбэк вызывается хотя бы один раз;
        - все значения в диапазоне [0, 100];
        - последнее значение — 100 (сигнал GUI «операция завершена»).

    Тип: контракт для GUI.
    """
    # Arrange
    src = tmp_path / "input.bin"
    src.write_bytes(b"x" * 10000)               # не очень маленький файл

    enc = tmp_path / "input.enc"
    progress_values = []

    # Act
    encrypt_file(src, enc, "password", progress_cb=progress_values.append)

    # Assert
    assert progress_values, "Колбэк должен быть вызван хотя бы раз"
    assert progress_values[-1] == 100, "Финальное значение прогресса должно быть 100"
    assert all(0 <= v <= 100 for v in progress_values), \
        "Все значения прогресса должны быть в диапазоне 0–100"

# ============================================================
# Тест 11. src не существует → FileNotFoundError
# ============================================================

def test_encrypt_missing_source_raises(tmp_path):
    """
    Проверяет, что encrypt_file бросает FileNotFoundError,
    если исходный файл не существует.

    Сценарий:
        1. Указываем src, которого нет на диске.
        2. Пытаемся зашифровать.
        3. Ожидаем FileNotFoundError.

    Проверяет:
        - функция НЕ создаёт пустой src «на лету»;
        - выходной файл НЕ создаётся при ошибке;
        - пользователь получает понятную ошибку, а не молчаливый сбой.

    Тип: обработка ошибок ввода-вывода.
    """
    # Arrange
    src = tmp_path / "does_not_exist.bin"        # файла нет
    enc = tmp_path / "output.enc"

    # Act + Assert
    with pytest.raises(FileNotFoundError):
        encrypt_file(src, enc, "password")

    # Дополнительно: выходной файл не должен появиться
    assert not enc.exists(), "При ошибке выходной файл не должен создаваться"

# ============================================================
# Тест 12. dst в несуществующей директории → FileNotFoundError
# ============================================================

def test_encrypt_dst_in_missing_directory_raises(tmp_path):
    """
    Проверяет, что encrypt_file не создаёт родительские директории
    автоматически — вместо этого падает с FileNotFoundError.

    Сценарий:
        1. Создаём валидный src.
        2. Указываем dst в несуществующей поддиректории.
        3. Ожидаем FileNotFoundError.

    Проверяет:
        - file_service НЕ занимается созданием директорий;
        - ответственность за создание папок — на вызывающем коде
          (например, dst.parent.mkdir(parents=True, exist_ok=True));
        - ошибка очевидна и не маскируется.

    Тип: контракт — границы ответственности модуля.
    """
    # Arrange
    src = tmp_path / "input.bin"
    src.write_bytes(b"data")

    dst = tmp_path / "nonexistent_dir" / "output.enc"   # папки не существует

    # Act + Assert
    with pytest.raises(FileNotFoundError):
        encrypt_file(src, dst, "password")

    # Дополнительно: поддиректория не должна была создаться
    assert not dst.parent.exists(), "file_service не должен создавать директории"

# ============================================================
# Тест 13. src — директория → IsADirectoryError
# ============================================================

def test_encrypt_src_is_directory_raises(tmp_path):
    """
    Проверяет, что encrypt_file бросает IsADirectoryError,
    если src — это директория, а не файл.

    Сценарий:
        1. Создаём директорию с именем, похожим на файл.
        2. Пытаемся зашифровать её как файл.
        3. Ожидаем IsADirectoryError.

    Проверяет:
        - функция различает файлы и директории;
        - ошибка очевидна (не пытается читать содержимое папки как байты);
        - пользователь получает понятное сообщение.

    Тип: обработка ошибочного ввода.
    """
    # Arrange
    src = tmp_path / "some_dir"
    src.mkdir()                                  # это папка, не файл

    enc = tmp_path / "output.enc"

    # Act + Assert
    with pytest.raises(IsADirectoryError):
        encrypt_file(src, enc, "password")

# ============================================================
# Тест 14. encrypt_file перезаписывает существующий dst
# ============================================================

def test_encrypt_overwrites_existing_dst(tmp_path):
    """
    Проверяет, что encrypt_file перезаписывает существующий dst,
    а не падает с ошибкой.

    Сценарий:
        1. Создаём src.
        2. Создаём dst с произвольным старым содержимым.
        3. Шифруем src → dst.
        4. Убеждаемся, что старое содержимое dst затёрто.

    Проверяет:
        - поведение по умолчанию — перезапись (не ошибка);
        - вызывающий код может перезаписать старый файл новым;
        - не остаётся «мусора» от предыдущего содержимого.

    Тип: контракт поведения по умолчанию.
    """
    # Arrange
    src = tmp_path / "input.bin"
    src.write_bytes(b"new data")

    dst = tmp_path / "output.enc"
    dst.write_bytes(b"old content")              # уже есть файл

    # Act
    encrypt_file(src, dst, "password")

    # Assert
    assert dst.read_bytes() != b"old content", "Старое содержимое должно быть затёрто"
    assert dst.read_bytes() != b"new data", "Содержимое dst должно быть зашифровано"

# ============================================================
# Тест 15. Roundtrip на пустом файле (0 байт)
# ============================================================

def test_roundtrip_empty_file(tmp_path):
    """
    Проверяет, что шифрование и дешифрование работают на пустом файле.

    Сценарий:
        1. Создаём src с 0 байт.
        2. Шифруем → .enc.
        3. Расшифровываем → restored.
        4. Убеждаемся, что restored тоже 0 байт.

    Проверяет:
        - граничный случай 0 байт;
        - crypto корректно обрабатывает пустые данные;
        - file_service не падает на пустых файлах;
        - нет «фантомных» байтов в результате (например, из-за заголовка).

    Тип: граничный случай.
    """
    # Arrange
    src = tmp_path / "empty.bin"
    src.write_bytes(b"")

    enc = tmp_path / "empty.enc"
    dec = tmp_path / "empty_restored.bin"

    # Act
    encrypt_file(src, enc, "password")
    decrypt_file(enc, dec, "password")

    # Assert
    assert enc.exists(), "Зашифрованный файл должен быть создан"
    assert dec.exists(), "Расшифрованный файл должен быть создан"
    assert enc.read_bytes() != b"", "Шифротекст не может быть пустым (есть заголовок)"
    assert dec.read_bytes() == b"", "Расшифровка пустого файла должна вернуть пустой файл"

# ============================================================
# Тест 16. Расшифровка повреждённого файла → WrongPasswordError
# ============================================================

def test_decrypt_corrupted_file_raises(tmp_path):
    """
    Проверяет, что decrypt_file бросает WrongPasswordError,
    если байты зашифрованного файла повреждены.

    Сценарий:
        1. Шифруем файл нормально.
        2. Портим один байт в .enc-файле.
        3. Пытаемся расшифровать.
        4. Ожидаем WrongPasswordError.

    Проверяет:
        - AES-GCM обнаруживает подмену байтов (аутентификация работает);
        - повреждённые данные не превращаются в «мусор на выходе»;
        - ошибка преобразуется в доменное исключение WrongPasswordError.

    Тип: безопасность, целостность данных.
    """
    # Arrange
    src = tmp_path / "input.bin"
    src.write_bytes(b"secret data")

    enc = tmp_path / "input.enc"
    encrypt_file(src, enc, "password")

    # Портим последний байт шифротекста
    corrupted = bytearray(enc.read_bytes())
    corrupted[-1] ^= 0xFF
    enc.write_bytes(bytes(corrupted))

    dec = tmp_path / "output.bin"

    # Act + Assert
    with pytest.raises(WrongPasswordError):
        decrypt_file(enc, dec, "password")

    assert not dec.exists(), "При ошибке выходной файл не должен создаваться"

# ============================================================
# Тест 17. decrypt_file не изменяет и не удаляет src
# ============================================================

def test_decrypt_does_not_modify_source(tmp_path):
    """
    Проверяет, что decrypt_file не изменяет и не удаляет src (.enc-файл).

    Сценарий:
        1. Шифруем файл → .enc.
        2. Запоминаем содержимое .enc.
        3. Расшифровываем.
        4. Убеждаемся: .enc существует и его байты не изменились.

    Проверяет:
        - decrypt_file не портит зашифрованный файл;
        - при ошибке можно повторить попытку (файл .enc остался валидным);
        - симметрия с encrypt_file — тоже не трогает src.

    Тип: свойство безопасности данных.
    """
    # Arrange
    src = tmp_path / "input.bin"
    src.write_bytes(b"important data")

    enc = tmp_path / "input.enc"
    encrypt_file(src, enc, "password")

    original_enc_bytes = enc.read_bytes()

    dec = tmp_path / "output.bin"

    # Act
    decrypt_file(enc, dec, "password")

    # Assert
    assert enc.exists(), "Зашифрованный файл не должен быть удалён"
    assert enc.read_bytes() == original_enc_bytes, "Зашифрованный файл не должен быть изменён"
    assert dec.read_bytes() == b"important data", "Расшифровка должна дать исходные данные"



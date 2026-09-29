from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def sample_docx(fixtures_dir):
    return fixtures_dir / "sample_2.docx", fixtures_dir / "sample_6.docx"


@pytest.fixture
def sample_xlsx(fixtures_dir):
    return fixtures_dir / "sample_1.xlsm", fixtures_dir / "sample_3.xlsx"


@pytest.fixture
def sample_jpg(fixtures_dir):
    return fixtures_dir / "sample_4.png", fixtures_dir / "sample_5.jpg"
def test_fixtures_debug(fixtures_dir, sample_docx, sample_xlsx, sample_jpg):
    print()
    print("fixtures_dir  =", fixtures_dir)
    print("sample_docx   =", sample_docx)
    print("sample_xlsx   =", sample_xlsx)
    print("sample_jpg    =", sample_jpg)

    # Проверим, что это Path
    print("тип:", type(sample_docx))

    # Проверим, существует ли файл
    print("существует sample_docx:", all([elem.exists() for elem in sample_docx]))
    print("существует sample_xlsx:", all([elem.exists() for elem in sample_xlsx]))
    print("существует sample_jpg :", all([elem.exists() for elem in sample_jpg]))
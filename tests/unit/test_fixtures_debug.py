def test_fixtures_debug(fixtures_dir, sample_docx_files, sample_xlsx_files, sample_jpg_files):
    print()
    print("fixtures_dir  =", fixtures_dir)
    print("sample_docx_file_files   =", sample_docx_files)
    print("sample_xlsx_file_files   =", sample_xlsx_files)
    print("sample_jpg_file_files    =", sample_jpg_files)

    # Проверим, что это Path
    print("тип:", type(sample_docx_files))

    # Проверим, существует ли файл
    print("существует sample_docx:", all([elem.exists() for elem in sample_docx_files]))
    print("существует sample_xlsx:", all([elem.exists() for elem in sample_xlsx_files]))
    print("существует sample_jpg :", all([elem.exists() for elem in sample_jpg_files]))
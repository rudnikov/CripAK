block_cipher = None

a = Analysis(
    ['../src/crypt_app/__main__.py'],
    pathex=['../src'],
    binaries=[],
    datas=[],
    hiddenimports=['cryptography'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt6.QtWebEngineCore'],
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='CryptApp',
    console=False,
    target_arch='arm64',   # или 'x86_64', или 'universal2'
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name='CryptApp')

app = BUNDLE(
    coll,
    name='CryptApp.app',
    icon='../assets/icon.icns',
    bundle_identifier='com.example.cryptapp',
    info_plist={
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'NSDocumentsFolderUsageDescription': 'Приложение шифрует файлы в ваших папках.',
    },
)
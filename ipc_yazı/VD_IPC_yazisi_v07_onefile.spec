# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['VD_IPC_yazisi_v07.py'],
    pathex=[],
    binaries=[],
    datas=[('sablonlar', 'sablonlar')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy',
        'PIL',
        'Pillow',
        'matplotlib',
        'pandas',
        'scipy',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VD_IPC_yazisi_v07_onefile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='vd_ipc_icon.ico',
    version='version_info_v04.txt',
)

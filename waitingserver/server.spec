# -*- mode: python ; coding: utf-8 -*-
from os.path import join, dirname, abspath, split
from os import sep
import glob

block_cipher = None

datas = [
    ( 'data/tags/*.bin', 'waitingserver/data/tags' )
]

a = Analysis(['__main__.py'],
             pathex=['.', '../venv/Lib/site-packages'],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='server',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )

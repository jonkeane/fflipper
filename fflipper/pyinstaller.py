import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_data_files
from pathlib import Path

HERE = Path(__file__).parent.absolute()
path_to_main = str(HERE / "fflipper.py")
path_to_ffmpeg = str(HERE / "bin" / "ffmpeg")

def install():
    PyInstaller.__main__.run([
        path_to_main,
        '--onefile',
        '--windowed',
        f'--add-data={path_to_ffmpeg}:bin',
        '--icon=logo/fflipper.icns',
        '--name', 'fflipper',
        '--hidden-import=_tkinter',
    ])
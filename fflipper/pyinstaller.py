import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_data_files
from pathlib import Path
import platform

HERE = Path(__file__).parent.absolute()
path_to_main = str(HERE / "fflipper.py")
sys = platform.system().lower()
if (sys == "darwin"):
    plat = platform.platform()
    if ("x86" in plat):
        platform_dir = "macos_x86"
    else:
        platform_dir = "macos_arm"

path_to_ffmpeg_binary = str(HERE / "bin" / platform_dir / "ffmpeg")

def install():
    PyInstaller.__main__.run([
        path_to_main,
        '--onefile',
        '--windowed',
        f'--add-data={path_to_ffmpeg_binary}:bin',
        '--icon=logo/fflipper.icns',
        '--name', 'fflipper',
        '--hidden-import=_tkinter',
    ])
"""
Build script to compile YouTube Downloader Pro into a SINGLE-FILE standalone Windows .exe
"""
import subprocess
import sys
import os

def build_onefile():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    icon_path = os.path.join(script_dir, "icon.ico")
    ffmpeg_path = os.path.join(script_dir, "bin", "ffmpeg.exe")
    ffprobe_path = os.path.join(script_dir, "bin", "ffprobe.exe")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name", "YouTubeDownloader_SingleFile",
        f"--icon={icon_path}",
        f"--add-data={icon_path};.",
        f"--add-binary={ffmpeg_path};bin",
        f"--add-binary={ffprobe_path};bin",
        "--collect-all", "customtkinter",
        "--collect-all", "yt_dlp",
        "--collect-all", "mutagen",
        "--hidden-import", "PIL",
        "--hidden-import", "requests",
        "--clean",
        "-y",
        "main.py"
    ]

    print("Tek dosya (OneFile) PyInstaller baslatiliyor...")
    res = subprocess.run(cmd)
    if res.returncode == 0:
        exe_file = os.path.join(script_dir, "dist", "YouTubeDownloader_SingleFile.exe")
        print(f"[OK] Tek dosya EXE hazir: {exe_file}")
    else:
        print(f"[HATA] Derleme hatasi! Kod: {res.returncode}")

if __name__ == "__main__":
    build_onefile()

"""
Build script to compile YouTube Downloader Pro into a standalone Windows .exe
"""
import subprocess
import sys
import os

def build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    icon_path = os.path.join(script_dir, "icon.ico")
    ffmpeg_path = os.path.join(script_dir, "bin", "ffmpeg.exe")
    ffprobe_path = os.path.join(script_dir, "bin", "ffprobe.exe")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onedir",
        "--name", "YouTubeDownloaderPro",
        f"--icon={icon_path}",
        f"--add-data={icon_path};.",
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

    print("PyInstaller başlatılıyor...")
    print("Komut:", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n✅ DERLEME BAŞARILI!")
        dist_dir = os.path.join(script_dir, "dist", "YouTubeDownloaderPro")
        exe_file = os.path.join(dist_dir, "YouTubeDownloaderPro.exe")
        print(f"Çıktı konumu: {exe_file}")
    else:
        print(f"\n❌ Derleme hatası! Kod: {res.returncode}")

if __name__ == "__main__":
    build()

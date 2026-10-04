"""
YouTube Downloader Pro - MP3 & MP4 Downloader
Modern desktop application built with CustomTkinter, yt-dlp, and FFmpeg.
"""

import os
import sys
import io
import time
import shutil
import threading
import subprocess
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import requests
from PIL import Image, ImageTk
import customtkinter as ctk
import yt_dlp


# ---------------------------------------------------------
# Helper Functions & Dependency Resolution
# ---------------------------------------------------------
def get_ffmpeg_directory():
    """Locate ffmpeg and ffprobe binaries."""
    # 1. PyInstaller frozen environment
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            meipass_bin = os.path.join(sys._MEIPASS, 'bin')
            if os.path.exists(os.path.join(meipass_bin, 'ffmpeg.exe')):
                return meipass_bin
            if os.path.exists(os.path.join(sys._MEIPASS, 'ffmpeg.exe')):
                return sys._MEIPASS

        exe_dir = os.path.dirname(sys.executable)
        internal_bin = os.path.join(exe_dir, '_internal', 'bin')
        if os.path.exists(os.path.join(internal_bin, 'ffmpeg.exe')):
            return internal_bin

        exe_bin = os.path.join(exe_dir, 'bin')
        if os.path.exists(os.path.join(exe_bin, 'ffmpeg.exe')):
            return exe_bin
        if os.path.exists(os.path.join(exe_dir, 'ffmpeg.exe')):
            return exe_dir

    # 2. Local bin folder next to script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_bin = os.path.join(script_dir, 'bin')
    if os.path.exists(os.path.join(local_bin, 'ffmpeg.exe')):
        return local_bin

    # 3. System PATH
    system_ffmpeg = shutil.which('ffmpeg')
    if system_ffmpeg:
        return os.path.dirname(system_ffmpeg)

    # 4. Standard known directories on this machine
    user_home = str(Path.home())
    possible_paths = [
        os.path.join(user_home, '.gemini', 'antigravity', 'bin'),
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin"
    ]
    for p in possible_paths:
        if os.path.exists(os.path.join(p, 'ffmpeg.exe')):
            return p

    return None


def get_default_download_folder():
    """Return user's standard Downloads folder."""
    user_home = Path.home()
    downloads = user_home / "Downloads"
    if downloads.exists():
        return str(downloads)
    # Turkish Windows fallback
    indirilenler = user_home / "İndirilenler"
    if indirilenler.exists():
        return str(indirilenler)
    return str(user_home)


def format_seconds(seconds):
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds or seconds < 0:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_bytes(bytes_num):
    """Format bytes to human-readable size (MB, GB, etc.)."""
    if not bytes_num or bytes_num <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"


class YtDlpCustomLogger:
    """Silent logger to prevent yt-dlp warning popups on console."""
    def __init__(self, callback=None):
        self.callback = callback

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        if self.callback:
            self.callback(msg)


# ---------------------------------------------------------
# Main Application GUI
# ---------------------------------------------------------
class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Appearance configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("YouTube MP3 & MP4 İndirici Pro")
        self.geometry("780x860")
        self.minsize(720, 800)

        # Set window icon if available
        self.set_app_icon()

        # State variables
        self.ffmpeg_dir = get_ffmpeg_directory()
        self.is_downloading = False
        self.cancel_requested = False
        self.current_video_info = None
        self.last_downloaded_file = None
        self.fetch_thread = None

        # Build UI
        self.create_widgets()

    def set_app_icon(self):
        """Set window icon from bundled or local files."""
        icon_candidates = []
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            icon_candidates.append(os.path.join(sys._MEIPASS, 'icon.ico'))
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_candidates.append(os.path.join(script_dir, 'icon.ico'))

        for icon_path in icon_candidates:
            if os.path.exists(icon_path):
                try:
                    self.iconbitmap(icon_path)
                    break
                except Exception:
                    pass

    def create_widgets(self):
        """Construct the complete user interface."""
        # Main scrollable or clean frame
        self.main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 15))

        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="both")

        self.lbl_title = ctk.CTkLabel(
            title_box,
            text="🎬 YouTube İndirici Pro",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=("#1f538d", "#38bdf8")
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_subtitle = ctk.CTkLabel(
            title_box,
            text="MP3 (320 kbps) ve MP4 (1080p 60FPS) Ultra Hızlı İndirme Aracı",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray50", "gray70")
        )
        self.lbl_subtitle.pack(anchor="w")

        # Theme Switcher
        self.theme_switch = ctk.CTkSwitch(
            self.header_frame,
            text="Koyu Tema",
            command=self.toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="right", padx=5, pady=5)

        # 2. URL Input Card
        self.url_card = ctk.CTkFrame(self.main_container, corner_radius=12)
        self.url_card.pack(fill="x", pady=(0, 15), ipady=5)

        lbl_url = ctk.CTkLabel(
            self.url_card,
            text="🔗 YouTube Video Bağlantısı:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl_url.pack(anchor="w", padx=16, pady=(10, 4))

        input_row = ctk.CTkFrame(self.url_card, fg_color="transparent")
        input_row.pack(fill="x", padx=16, pady=(0, 10))

        self.entry_url = ctk.CTkEntry(
            input_row,
            placeholder_text="https://www.youtube.com/watch?v=... veya https://youtu.be/...",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_url.bind("<Return>", lambda event: self.start_fetch_info())

        self.btn_paste = ctk.CTkButton(
            input_row,
            text="📋 Yapıştır",
            width=90,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.paste_from_clipboard
        )
        self.btn_paste.pack(side="left", padx=(0, 8))

        self.btn_fetch = ctk.CTkButton(
            input_row,
            text="🔍 Bilgi Getir",
            width=100,
            height=40,
            fg_color="#0284c7",
            hover_color="#0369a1",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_fetch_info
        )
        self.btn_fetch.pack(side="left")

        # 3. Video Preview Card
        self.preview_card = ctk.CTkFrame(self.main_container, corner_radius=12)
        self.preview_card.pack(fill="x", pady=(0, 15))

        self.preview_inner = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.preview_inner.pack(fill="both", expand=True, padx=14, pady=12)

        # Thumbnail Label
        self.lbl_thumbnail = ctk.CTkLabel(
            self.preview_inner,
            text="🖼️\nÖnizleme",
            width=160,
            height=90,
            corner_radius=8,
            fg_color=("gray85", "gray25"),
            font=ctk.CTkFont(size=12)
        )
        self.lbl_thumbnail.pack(side="left", padx=(0, 14))

        # Video Info Texts
        self.info_box = ctk.CTkFrame(self.preview_inner, fg_color="transparent")
        self.info_box.pack(side="left", fill="both", expand=True)

        self.lbl_video_title = ctk.CTkLabel(
            self.info_box,
            text="Video bekleniyor...",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=480
        )
        self.lbl_video_title.pack(anchor="w", fill="x", pady=(0, 4))

        self.lbl_video_channel = ctk.CTkLabel(
            self.info_box,
            text="👤 Kanal: -",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray70"),
            anchor="w"
        )
        self.lbl_video_channel.pack(anchor="w")

        self.lbl_video_duration = ctk.CTkLabel(
            self.info_box,
            text="⏱️ Süre: -",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray70"),
            anchor="w"
        )
        self.lbl_video_duration.pack(anchor="w")

        self.lbl_video_status_badge = ctk.CTkLabel(
            self.info_box,
            text="Bir YouTube bağlantısı girin ve indirme formatını seçin",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color=("gray50", "gray60"),
            anchor="w"
        )
        self.lbl_video_status_badge.pack(anchor="w", pady=(4, 0))

        # 4. Format Selection Card (MP3 vs MP4)
        self.format_card = ctk.CTkFrame(self.main_container, corner_radius=12)
        self.format_card.pack(fill="x", pady=(0, 15), ipady=8)

        lbl_format_title = ctk.CTkLabel(
            self.format_card,
            text="🎯 İndirme Formatı:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl_format_title.pack(anchor="w", padx=16, pady=(10, 8))

        self.format_segmented = ctk.CTkSegmentedButton(
            self.format_card,
            values=["🎵 MP3 (Sadece Ses)", "🎬 MP4 (Video ve Ses)"],
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            command=self.on_format_changed
        )
        self.format_segmented.set("🎵 MP3 (Sadece Ses)")
        self.format_segmented.pack(fill="x", padx=16, pady=(0, 12))

        # Dynamic options container
        self.options_container = ctk.CTkFrame(self.format_card, fg_color=("gray90", "gray18"), corner_radius=10)
        self.options_container.pack(fill="x", padx=16, pady=(0, 10), ipady=6)

        # --- MP3 Sub-frame ---
        self.frame_mp3_options = ctk.CTkFrame(self.options_container, fg_color="transparent")

        lbl_mp3_quality = ctk.CTkLabel(
            self.frame_mp3_options,
            text="🔊 Ses Kalitesi (Bitrate):",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_mp3_quality.pack(anchor="w", padx=14, pady=(8, 4))

        self.mp3_quality_options = [
            "320 kbps (En Yüksek / Stüdyo Kalitesi)",
            "256 kbps (Çok Yüksek Kalite)",
            "192 kbps (Yüksek Kalite - Standart)",
            "128 kbps (Orta Kalite - Küçük Boyut)",
            "64 kbps (Düşük Kalite / Konuşma İçin)"
        ]
        self.opt_mp3_quality = ctk.CTkOptionMenu(
            self.frame_mp3_options,
            values=self.mp3_quality_options,
            height=36,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12)
        )
        self.opt_mp3_quality.set("320 kbps (En Yüksek / Stüdyo Kalitesi)")
        self.opt_mp3_quality.pack(fill="x", padx=14, pady=(0, 10))

        self.chk_mp3_thumbnail = ctk.CTkCheckBox(
            self.frame_mp3_options,
            text="🖼️ Albüm kapak resmini ve sanatçı etiketlerini MP3 dosyasına göm",
            font=ctk.CTkFont(size=12)
        )
        self.chk_mp3_thumbnail.select()
        self.chk_mp3_thumbnail.pack(anchor="w", padx=14, pady=(0, 8))

        # --- MP4 Sub-frame ---
        self.frame_mp4_options = ctk.CTkFrame(self.options_container, fg_color="transparent")

        lbl_mp4_quality = ctk.CTkLabel(
            self.frame_mp4_options,
            text="📺 Video Çözünürlüğü ve Kare Hızı (FPS):",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_mp4_quality.pack(anchor="w", padx=14, pady=(8, 4))

        self.mp4_quality_options = [
            "En Yüksek Kalite (Mevcut En İyi Çözünürlük)",
            "1080p 60FPS (Full HD Akıcı)",
            "1080p 30FPS (Full HD Standart)",
            "720p 60FPS (HD Akıcı)",
            "720p 30FPS (HD Standart)",
            "480p 30FPS (SD Standart)",
            "360p 30FPS (Düşük Boyut)"
        ]
        self.opt_mp4_quality = ctk.CTkOptionMenu(
            self.frame_mp4_options,
            values=self.mp4_quality_options,
            height=36,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12)
        )
        self.opt_mp4_quality.set("1080p 60FPS (Full HD Akıcı)")
        self.opt_mp4_quality.pack(fill="x", padx=14, pady=(0, 10))

        self.chk_mp4_subtitles = ctk.CTkCheckBox(
            self.frame_mp4_options,
            text="📑 Varsa Türkçe/İngilizce Altyazıları İndir",
            font=ctk.CTkFont(size=12)
        )
        self.chk_mp4_subtitles.pack(anchor="w", padx=14, pady=(0, 8))

        # Pack default MP3 view
        self.frame_mp3_options.pack(fill="x", expand=True)

        # 5. Save Directory Card
        self.dir_card = ctk.CTkFrame(self.main_container, corner_radius=12)
        self.dir_card.pack(fill="x", pady=(0, 15), ipady=5)

        lbl_dir = ctk.CTkLabel(
            self.dir_card,
            text="📁 Kayıt Konumu:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl_dir.pack(anchor="w", padx=16, pady=(10, 4))

        dir_row = ctk.CTkFrame(self.dir_card, fg_color="transparent")
        dir_row.pack(fill="x", padx=16, pady=(0, 10))

        self.entry_dir = ctk.CTkEntry(
            dir_row,
            height=38,
            font=ctk.CTkFont(size=12)
        )
        self.entry_dir.insert(0, get_default_download_folder())
        self.entry_dir.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_browse = ctk.CTkButton(
            dir_row,
            text="📂 Değiştir...",
            width=100,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.browse_directory
        )
        self.btn_browse.pack(side="left", padx=(0, 8))

        self.btn_open_folder = ctk.CTkButton(
            dir_row,
            text="🔍 Klasörü Aç",
            width=100,
            height=38,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            font=ctk.CTkFont(size=12),
            command=self.open_current_directory
        )
        self.btn_open_folder.pack(side="left")

        # 6. Progress and Status Card
        self.progress_card = ctk.CTkFrame(self.main_container, corner_radius=12)
        self.progress_card.pack(fill="x", pady=(0, 15), ipady=6)

        # Status text row
        status_row = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(10, 4))

        self.lbl_status = ctk.CTkLabel(
            status_row,
            text="Durum: Hazır",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        self.lbl_status.pack(side="left", fill="x", expand=True)

        self.lbl_percent = ctk.CTkLabel(
            status_row,
            text="%0",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1f538d", "#38bdf8")
        )
        self.lbl_percent.pack(side="right")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.progress_card, height=12)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=16, pady=(4, 6))

        # Speed, ETA and Size row
        detail_row = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        detail_row.pack(fill="x", padx=16, pady=(0, 10))

        self.lbl_speed_eta = ctk.CTkLabel(
            detail_row,
            text="Hız: -  |  Kalan Süre: -",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            anchor="w"
        )
        self.lbl_speed_eta.pack(side="left")

        self.lbl_file_size = ctk.CTkLabel(
            detail_row,
            text="İndirilen: 0 MB / 0 MB",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            anchor="e"
        )
        self.lbl_file_size.pack(side="right")

        # 7. Action Buttons
        self.action_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.action_frame.pack(fill="x", pady=(0, 10))

        self.btn_download = ctk.CTkButton(
            self.action_frame,
            text="⬇️ İndirmeyi Başlat",
            height=48,
            fg_color="#16a34a",
            hover_color="#15803d",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_download
        )
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_cancel = ctk.CTkButton(
            self.action_frame,
            text="⏹️ İptal Et",
            height=48,
            width=120,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=self.cancel_download
        )
        self.btn_cancel.pack(side="left")

        # 8. Bottom Information / Help Bar
        self.footer_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.footer_frame.pack(fill="x", pady=(5, 0))

        ffmpeg_status = "✅ FFmpeg Aktif" if self.ffmpeg_dir else "⚠️ FFmpeg Bulunamadı (Bazı formatlar sınırlı olabilir)"
        ffmpeg_color = "#16a34a" if self.ffmpeg_dir else "#ca8a04"

        self.lbl_ffmpeg_status = ctk.CTkLabel(
            self.footer_frame,
            text=ffmpeg_status,
            font=ctk.CTkFont(size=11),
            text_color=ffmpeg_color
        )
        self.lbl_ffmpeg_status.pack(side="left")

        self.lbl_version = ctk.CTkLabel(
            self.footer_frame,
            text="yt-dlp Entegre • Python 3.14",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        )
        self.lbl_version.pack(side="right")

    # ---------------------------------------------------------
    # Event Handlers & UI Logic
    # ---------------------------------------------------------
    def toggle_theme(self):
        """Switch between dark and light themes."""
        if self.theme_switch.get() == "dark":
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="Koyu Tema")
        else:
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="Açık Tema")

    def on_format_changed(self, selected_mode):
        """Switch dynamic settings frame between MP3 and MP4."""
        if "MP3" in selected_mode:
            self.frame_mp4_options.pack_forget()
            self.frame_mp3_options.pack(fill="x", expand=True)
        else:
            self.frame_mp3_options.pack_forget()
            self.frame_mp4_options.pack(fill="x", expand=True)

    def browse_directory(self):
        """Open directory chooser dialog."""
        folder = filedialog.askdirectory(initialdir=self.entry_dir.get())
        if folder:
            self.entry_dir.delete(0, tk.END)
            self.entry_dir.insert(0, folder)

    def open_current_directory(self):
        """Open the target folder in Windows Explorer."""
        folder = self.entry_dir.get().strip()
        if os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Hata", f"Klasör açılamadı: {e}")
        else:
            messagebox.showwarning("Uyarı", "Seçilen kayıt klasörü mevcut değil.")

    def paste_from_clipboard(self):
        """Paste URL from clipboard and trigger metadata fetching."""
        try:
            clipboard_text = self.clipboard_get().strip()
            if clipboard_text:
                self.entry_url.delete(0, tk.END)
                self.entry_url.insert(0, clipboard_text)
                self.start_fetch_info()
        except Exception:
            pass

    # ---------------------------------------------------------
    # Asynchronous Video Metadata Fetching
    # ---------------------------------------------------------
    def start_fetch_info(self):
        """Spawn thread to fetch video details."""
        url = self.entry_url.get().strip()
        if not url:
            return

        if self.fetch_thread and self.fetch_thread.is_alive():
            return

        self.lbl_video_status_badge.configure(
            text="⏳ Video bilgileri alınıyor...",
            text_color=("#1f538d", "#38bdf8")
        )
        self.btn_fetch.configure(state="disabled")

        self.fetch_thread = threading.Thread(target=self._worker_fetch_info, args=(url,), daemon=True)
        self.fetch_thread.start()

    def _worker_fetch_info(self, url):
        """Worker thread to query yt-dlp for video metadata."""
        try:
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'no_warnings': True,
                'noplaylist': True,
                'logger': YtDlpCustomLogger(),
            }
            if self.ffmpeg_dir:
                ydl_opts['ffmpeg_location'] = self.ffmpeg_dir

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.after(0, self._on_info_fetched_success, info)
        except Exception as e:
            err_msg = str(e)
            if "not a valid URL" in err_msg or "Unsupported url" in err_msg:
                err_msg = "Geçersiz YouTube bağlantısı."
            self.after(0, self._on_info_fetched_error, err_msg)

    def _on_info_fetched_success(self, info):
        """Update preview UI upon successful metadata fetch."""
        self.btn_fetch.configure(state="normal")
        self.current_video_info = info

        title = info.get('title', 'Bilinmeyen Başlık')
        uploader = info.get('uploader') or info.get('channel') or 'Bilinmiyor'
        duration = format_seconds(info.get('duration', 0))
        thumbnail_url = info.get('thumbnail')

        self.lbl_video_title.configure(text=title)
        self.lbl_video_channel.configure(text=f"👤 Kanal: {uploader}")
        self.lbl_video_duration.configure(text=f"⏱️ Süre: {duration}")
        self.lbl_video_status_badge.configure(
            text="✅ Video bilgileri doğrulandı. İndirmeye hazır!",
            text_color=("#16a34a", "#22c55e")
        )

        # Download thumbnail asynchronously
        if thumbnail_url:
            threading.Thread(target=self._load_thumbnail_async, args=(thumbnail_url,), daemon=True).start()

    def _load_thumbnail_async(self, thumb_url):
        """Fetch thumbnail image bytes and display in UI."""
        try:
            resp = requests.get(thumb_url, timeout=5)
            if resp.status_code == 200:
                raw_img = Image.open(io.BytesIO(resp.content))
                # Target aspect ratio: 160 x 90
                raw_img = raw_img.resize((160, 90), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(160, 90))
                self.after(0, self._set_thumbnail_image, ctk_img)
        except Exception:
            pass

    def _set_thumbnail_image(self, ctk_img):
        self.lbl_thumbnail.configure(image=ctk_img, text="")

    def _on_info_fetched_error(self, error_message):
        """Handle metadata fetch error."""
        self.btn_fetch.configure(state="normal")
        self.lbl_video_status_badge.configure(
            text=f"❌ Bilgi alınamadı: {error_message[:45]}...",
            text_color=("#dc2626", "#ef4444")
        )

    # ---------------------------------------------------------
    # Format Selector Generation
    # ---------------------------------------------------------
    def get_mp4_format_spec(self, selection):
        """Map user selection to resilient yt-dlp format strings with graceful fallbacks."""
        if "1080p 60FPS" in selection:
            # Prefer 1080p 60fps; fallback to regular 1080p, then best available
            return "bestvideo[height<=1080][fps>30]+bestaudio/bestvideo[height<=1080]+bestaudio/best"
        elif "1080p 30FPS" in selection:
            # Strictly select 1080p at 30fps or lower
            return "bestvideo[height<=1080][fps<=30]+bestaudio/bestvideo[height<=1080]+bestaudio/best"
        elif "720p 60FPS" in selection:
            return "bestvideo[height<=720][fps>30]+bestaudio/bestvideo[height<=720]+bestaudio/best"
        elif "720p 30FPS" in selection:
            return "bestvideo[height<=720][fps<=30]+bestaudio/bestvideo[height<=720]+bestaudio/best"
        elif "480p" in selection:
            return "bestvideo[height<=480]+bestaudio/bestvideo[height<=480]+bestaudio/best"
        elif "360p" in selection:
            return "bestvideo[height<=360]+bestaudio/bestvideo[height<=360]+bestaudio/best"
        else:
            # En İyi Kalite (Mevcut En Yüksek)
            return "bestvideo+bestaudio/best"

    def get_mp3_bitrate_spec(self, selection):
        """Extract bitrate number string for FFmpegExtractAudio."""
        if "320" in selection:
            return "320"
        elif "256" in selection:
            return "256"
        elif "192" in selection:
            return "192"
        elif "128" in selection:
            return "128"
        elif "64" in selection:
            return "64"
        return "320"

    # ---------------------------------------------------------
    # Download Execution & Threading
    # ---------------------------------------------------------
    def start_download(self):
        """Validate inputs and launch download worker thread."""
        url = self.entry_url.get().strip()
        if not url:
            messagebox.showwarning("Eksik Bilgi", "Lütfen bir YouTube bağlantısı girin.")
            return

        save_dir = self.entry_dir.get().strip()
        if not save_dir:
            save_dir = get_default_download_folder()
            self.entry_dir.insert(0, save_dir)

        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Hata", f"Hedef klasör oluşturulamadı:\n{e}")
                return

        # Prepare UI for download state
        self.is_downloading = True
        self.cancel_requested = False
        self.btn_download.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.btn_fetch.configure(state="disabled")
        self.progress_bar.set(0.0)
        self.lbl_percent.configure(text="%0")
        self.lbl_status.configure(text="Durum: İndirme başlatılıyor...", text_color=("#1f538d", "#38bdf8"))
        self.lbl_speed_eta.configure(text="Hız: Hesaplanıyor...  |  Kalan Süre: -")
        self.lbl_file_size.configure(text="İndirilen: 0 MB / -")

        # Spawn download thread
        threading.Thread(target=self._worker_download, args=(url, save_dir), daemon=True).start()

    def cancel_download(self):
        """Request immediate download abort."""
        if self.is_downloading:
            self.cancel_requested = True
            self.lbl_status.configure(text="Durum: İptal ediliyor...", text_color=("#dc2626", "#ef4444"))
            self.btn_cancel.configure(state="disabled")

    def _worker_download(self, url, save_dir):
        """Worker thread executing yt-dlp download pipeline."""
        selected_mode = self.format_segmented.get()
        is_mp3 = "MP3" in selected_mode

        # Progress hook
        def progress_hook(d):
            if self.cancel_requested:
                raise Exception("DOWNLOAD_CANCELLED_BY_USER")

            status = d.get('status')
            if status == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                speed = d.get('speed') or 0
                eta = d.get('eta') or 0

                # Calculate progress
                ratio = 0.0
                percent_str = "%0"
                if total > 0:
                    ratio = min(1.0, downloaded / total)
                    percent_str = f"%{ratio * 100:.1f}"
                elif downloaded > 0:
                    percent_str = f"{format_bytes(downloaded)}"

                speed_str = f"{format_bytes(speed)}/s" if speed else "-"
                eta_str = f"{format_seconds(eta)}" if eta else "-"
                size_str = f"{format_bytes(downloaded)} / {format_bytes(total) if total else '?'}"

                self.after(0, self._update_progress_ui, ratio, percent_str, speed_str, eta_str, size_str)

            elif status == 'finished':
                filename = d.get('filename')
                if filename:
                    self.last_downloaded_file = filename
                self.after(0, self._on_download_finished_stage)

        # Postprocessor hook for FFmpeg conversion updates
        def postprocessor_hook(d):
            if self.cancel_requested:
                raise Exception("DOWNLOAD_CANCELLED_BY_USER")

            status = d.get('status')
            postprocessor = d.get('postprocessor', '')
            if status == 'started':
                if 'ExtractAudio' in postprocessor:
                    msg = "Durum: FFmpeg ile MP3 formatına dönüştürülüyor..."
                elif 'Merger' in postprocessor:
                    msg = "Durum: Video ve Ses akışları birleştiriliyor (MP4)..."
                elif 'EmbedThumbnail' in postprocessor:
                    msg = "Durum: Kapak resmi gömülüyor..."
                else:
                    msg = f"Durum: İşleniyor ({postprocessor})..."
                self.after(0, lambda m=msg: self.lbl_status.configure(text=m, text_color=("#0284c7", "#38bdf8")))

        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': os.path.join(save_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [postprocessor_hook],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'restrictfilenames': False,
            'windowsfilenames': True,
            'logger': YtDlpCustomLogger(),
        }

        if self.ffmpeg_dir:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_dir

        if is_mp3:
            # MP3 Configuration
            bitrate = self.get_mp3_bitrate_spec(self.opt_mp3_quality.get())
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': bitrate,
            }]

            if self.chk_mp3_thumbnail.get() == 1:
                ydl_opts['writethumbnail'] = True
                postprocessors.append({'key': 'FFmpegMetadata'})
                postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})

            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = postprocessors

        else:
            # MP4 Configuration
            format_spec = self.get_mp4_format_spec(self.opt_mp4_quality.get())
            ydl_opts['format'] = format_spec
            ydl_opts['merge_output_format'] = 'mp4'

            if self.chk_mp4_subtitles.get() == 1:
                ydl_opts['writesubtitles'] = True
                ydl_opts['subtitleslangs'] = ['tr', 'en']
                ydl_opts['subtitlesformat'] = 'srt/vtt/best'

        # Execute download
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info_dict)
                if is_mp3:
                    downloaded_file = os.path.splitext(downloaded_file)[0] + ".mp3"
                else:
                    downloaded_file = os.path.splitext(downloaded_file)[0] + ".mp4"

                self.last_downloaded_file = downloaded_file
                self.after(0, self._on_download_complete_success, downloaded_file)

        except Exception as e:
            err_text = str(e)
            if "DOWNLOAD_CANCELLED_BY_USER" in err_text:
                self.after(0, self._on_download_cancelled)
            else:
                self.after(0, self._on_download_error, err_text)

    def _update_progress_ui(self, ratio, percent_str, speed_str, eta_str, size_str):
        """Thread-safe UI update for progress values."""
        self.progress_bar.set(ratio)
        self.lbl_percent.configure(text=percent_str)
        self.lbl_status.configure(text=f"Durum: İndiriliyor... ({percent_str})", text_color=("#1f538d", "#38bdf8"))
        self.lbl_speed_eta.configure(text=f"Hız: {speed_str}  |  Kalan Süre: {eta_str}")
        self.lbl_file_size.configure(text=f"İndirilen: {size_str}")

    def _on_download_finished_stage(self):
        """Download phase completed, entering postprocessing."""
        self.progress_bar.set(1.0)
        self.lbl_percent.configure(text="%100")
        self.lbl_status.configure(text="Durum: İndirme bitti, dosya işleniyor...", text_color=("#0284c7", "#38bdf8"))

    def _on_download_complete_success(self, target_filepath):
        """Called when download and all conversions have fully finished."""
        self.is_downloading = False
        self.btn_download.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        self.btn_fetch.configure(state="normal")
        self.progress_bar.set(1.0)
        self.lbl_percent.configure(text="%100")
        self.lbl_status.configure(text="Durum: 🎉 İndirme ve Dönüştürme Başarıyla Tamamlandı!", text_color=("#16a34a", "#22c55e"))

        filename = os.path.basename(target_filepath)
        response = messagebox.askyesno(
            "İşlem Tamamlandı",
            f"Dosyanız başarıyla indirildi:\n\n{filename}\n\nİndirilen dosyayı klasörde görüntülemek ister misiniz?"
        )
        if response and os.path.exists(target_filepath):
            try:
                # Open Explorer and select the specific file
                subprocess.Popen(f'explorer /select,"{os.path.abspath(target_filepath)}"')
            except Exception:
                try:
                    os.startfile(os.path.dirname(target_filepath))
                except Exception:
                    pass

    def _on_download_cancelled(self):
        """Called when user cancels the download."""
        self.is_downloading = False
        self.cancel_requested = False
        self.btn_download.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        self.btn_fetch.configure(state="normal")
        self.lbl_status.configure(text="Durum: İndirme kullanıcı tarafından iptal edildi.", text_color=("#dc2626", "#ef4444"))

    def _on_download_error(self, err_msg):
        """Called when a fatal error occurs during download."""
        self.is_downloading = False
        self.btn_download.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        self.btn_fetch.configure(state="normal")
        self.lbl_status.configure(text="Durum: ❌ Hata oluştu!", text_color=("#dc2626", "#ef4444"))

        clean_error = err_msg
        if "No supported JavaScript runtime" in clean_error:
            clean_error = "YouTube biçim çözümlenirken JavaScript runtime uyarısı alındı."

        messagebox.showerror("İndirme Hatası", f"İndirme sırasında bir hata oluştu:\n\n{clean_error[:300]}")


# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()

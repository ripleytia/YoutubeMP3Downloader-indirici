# 🎬 YouTube Downloader Pro (MP3 & MP4)

YouTube üzerinden yüksek hızda, kayıpsız ve kaliteli şekilde **MP3 (Ses)** ve **MP4 (Video)** indirmek için geliştirilmiş modern masaüstü uygulaması.

---

## 🌟 Özellikler

- **Modern ve Şık Arayüz:** CustomTkinter ile tasarlanmış koyu (Dark) ve açık (Light) tema destekli arayüz.
- **Tek Tıkla Bağlantı Yapıştırma:** Pano (Clipboard) entegrasyonu ile bağlantıyı anında algılama.
- **Otomatik Video Bilgi & Kapak Kartı:** Başlık, kanal adı, video süresi ve kapak resmini anında önizleme.
- **MP3 Ses İndirme Seçenekleri:**
  - `320 kbps` (En Yüksek / Stüdyo Kalitesi)
  - `256 kbps` (Çok Yüksek Kalite)
  - `192 kbps` (Yüksek Kalite - Standart)
  - `128 kbps` (Orta Kalite - Küçük Boyut)
  - `64 kbps` (Düşük Kalite / Konuşma İçin)
  - Albüm kapağı ve ID3 etiketlerini (Sanatçı, Başlık) otomatik gömme seçeneği.
- **MP4 Video & FPS Seçenekleri:**
  - `En Yüksek Kalite` (Mevcut en yüksek çözünürlük)
  - `1080p 60FPS` (Full HD Akıcı)
  - `1080p 30FPS` (Full HD Standart)
  - `720p 60FPS` (HD Akıcı)
  - `720p 30FPS` (HD Standart)
  - `480p 30FPS` (SD Kalite)
  - `360p 30FPS` (Düşük Boyut)
  - İsteğe bağlı altyazı indirme desteği.
- **Gelişmiş İndirme Yönetimi:**
  - Anlık indirme hızı (MB/s), kalan süre (ETA) ve indirilen veri yüzdesi.
  - Kesintisiz çok iş parçacıklı (Multi-threading) mimari: İndirme esnasında arayüz asla donmaz.
  - İndirmeyi dilediğiniz an iptal edebilme imkanı.
  - İndirme tamamlandığında Windows Gezgini'nde dosyayı otomatik seçerek gösterme seçeneği.
- **Tam Bağımsız .EXE:** FFmpeg motoru entegre edilmiş, harici kurulum gerektirmeyen çalıştırılabilir dosya.

---

## 🚀 Kurulum ve Çalıştırma

### 1. Python İle Doğrudan Çalıştırma:
```bash
pip install -r requirements.txt
python main.py
```

### 2. .EXE Olarak Derleme:
```bash
python build_exe.py
```
Derleme tamamlandığında çıktınız `dist/YouTubeDownloaderPro/YouTubeDownloaderPro.exe` konumunda hazır olacaktır.

---

## 🛠️ Kullanılan Teknolojiler

- **Arayüz:** CustomTkinter & Tkinter (Python)
- **Motor:** `yt-dlp` (En güncel YouTube API ve akış desteği)
- **Dönüştürücü:** `FFmpeg` 9.0.1 (Ses kodlama, muxing, yüksek bitrate MP3 ve 60FPS MP4 birleştirme)
- **Görsel & Etiketleme:** Pillow (PIL), Mutagen

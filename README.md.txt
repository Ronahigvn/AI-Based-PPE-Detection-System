# 🛡️ AI Tabanlı İş Güvenliği (KKD) Denetim Sistemi

Bu proje, ESP32-CAM ve YOLOv8 kullanılarak geliştirilmiş gerçek zamanlı bir **Kişisel Koruyucu Ekipman (KKD)** tespit ve uyarı sistemidir. İnşaat sahalarında baret ve yelek ihlallerini tespit ederek görsel/işitsel alarm verir.

## 🚀 Özellikler
- **Gerçek Zamanlı Tespit:** YOLOv8 modeli ile baret ve yelek kontrolü.
- **IoT Entegrasyonu:** ESP32-CAM üzerinden görüntü aktarımı ve donanım kontrolü.
- **Web Dashboard:** Canlı izleme, istatistik grafikleri ve sistem kontrolü.
- **Akıllı Alarm:** İhlal durumunda otomatik Buzzer ve LED tetikleme.

## 🛠️ Kullanılan Teknolojiler
- **Donanım:** ESP32-CAM, USB-TTL, Buzzer, LED
- **Yazılım:** Python, Flask, OpenCV
- **Yapay Zeka:** Roboflow, YOLOv8

## 📷 Ekran Görüntüleri


## ⚙️ Kurulum
1. Repoyu klonlayın.
2. Gerekli kütüphaneleri yükleyin: `pip install -r requirements.txt`
3. `app.py` dosyasındaki `API_KEY` alanına kendi Roboflow anahtarınızı girin.
4. Sunucuyu başlatın: `python app.py`

---
*Bu proje Bilgisayar Mühendisliği Gömülü ve Gerçek Zamanlı Ders  kapsamında geliştirilmiştir.*
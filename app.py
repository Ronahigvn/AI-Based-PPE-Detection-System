from flask import Flask, request, jsonify, Response, render_template_string
import cv2
import numpy as np
from roboflow import Roboflow
import threading
import time

# ================= AYARLAR =================
API_KEY = "Api Key Anahtarınızı Giriniz"
PROJECT_NAME = "personal-protective-equipment-combined-model"
VERSION = 8

app = Flask(__name__)

# İstatistik Sayaçları
total_safe = 0      # Güvenli tespit sayısı
total_violation = 0 # İhlal sayısı

# Global Değişkenler
global_frame = None  # İşlenmiş (kutulu) son resim
alarm_status = False # Alarm var mı yok mu?

print("🤖 Model yükleniyor...")
rf = Roboflow(api_key=API_KEY)
model = rf.workspace().project(PROJECT_NAME).version(VERSION).model
print("✅ Model Hazır! Sunucu başlatılıyor...")

# ================= HTML TASARIMI (SIFIRLA BUTONU EKLENDİ) =================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Güvenlik Paneli</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #e2e8f0;
            --accent-color: #3b82f6;
            --danger-color: #ef4444;
            --success-color: #22c55e;
            --border-color: #334155;
        }

        body { 
            background-color: var(--bg-color); 
            color: var(--text-color); 
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background-color: var(--card-bg);
            padding: 1rem 2rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            flex-shrink: 0;
        }

        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-controls {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .status-badge {
            background-color: rgba(34, 197, 94, 0.2);
            color: var(--success-color);
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid var(--success-color);
        }

        /* SIFIRLA BUTONU STİLİ */
        .reset-btn {
            background-color: var(--card-bg);
            color: #94a3b8;
            border: 1px solid var(--border-color);
            padding: 5px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }
        .reset-btn:hover {
            background-color: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }

        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 30px;
            overflow-y: auto;
        }

        /* --- YAN YANA DÜZEN --- */
        .content-row {
            display: flex;
            flex-direction: row;
            flex-wrap: wrap;
            justify-content: center;
            align-items: stretch; 
            gap: 25px;
            width: 100%;
            max-width: 1300px;
            margin-bottom: 30px;
        }

        /* VİDEO KUTUSU */
        .video-wrapper {
            position: relative;
            background-color: #000;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            border: 2px solid var(--border-color);
            transition: border-color 0.3s ease;
            flex: 1 1 450px; 
            max-width: 100%;
            display: flex;
            align-items: center; 
        }

        #video-stream {
            width: 100%;
            height: auto;
            border-radius: 8px;
            display: block;
            max-height: 400px;
            object-fit: contain;
        }

        .live-indicator {
            position: absolute;
            top: 20px;
            right: 20px;
            background-color: rgba(239, 68, 68, 0.9);
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 6px;
            z-index: 10;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            background-color: white;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }

        /* GRAFİK KUTUSU */
        .chart-container {
            background-color: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            flex: 1 1 450px;
            max-width: 100%;
            height: 420px; 
            display: flex;
            justify-content: center;
            align-items: center;
        }

        /* ALARM KUTUSU */
        #alarm-box {
            display: none;
            background: linear-gradient(45deg, #7f1d1d, #ef4444);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            width: 90%;
            max-width: 950px; 
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
            border: 2px solid #fecaca;
            animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
        }
        
        .stats-footer {
            margin-top: auto;
            padding: 20px;
            color: #64748b;
            font-size: 0.8rem;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }

        @keyframes shake {
            10%, 90% { transform: translate3d(-1px, 0, 0); }
            20%, 80% { transform: translate3d(2px, 0, 0); }
            30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
            40%, 60% { transform: translate3d(4px, 0, 0); }
        }

    </style>
</head>
<body>

    <header>
        <div class="logo">
            <span>🛡️</span> ŞANTİYE GÜVENLİK SİSTEMİ
        </div>
        <div class="header-controls">
            <button class="reset-btn" onclick="resetStats()">🔄 İstatistikleri Sıfırla</button>
            <div class="status-badge">● SİSTEM AKTİF</div>
        </div>
    </header>

    <div class="main-container">
        
        <div class="content-row">
            <div class="video-wrapper" id="video-border">
                <div class="live-indicator">
                    <div class="live-dot"></div> CANLI
                </div>
                <img id="video-stream" src="/video_feed" alt="Kamera Akışı">
            </div>

            <div class="chart-container">
                <canvas id="myChart"></canvas>
            </div>
        </div>

        <div id="alarm-box">
            ⚠️ İHLAL TESPİT EDİLDİ! <br>
            <span style="font-size: 1rem; font-weight: normal;">Lütfen koruyucu ekipmanları kontrol ediniz.</span>
        </div>

        <div class="stats-footer">
            Yapay Zeka Destekli Görüntü İşleme Modülü v1.0
        </div>
    </div>

    <script>
        // Grafik Oluşturma
        const ctx = document.getElementById('myChart').getContext('2d');
        const myChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Güvenli Tespit', 'İhlal Tespiti'],
                datasets: [{
                    label: 'Kişi Sayısı',
                    data: [1, 0], 
                    backgroundColor: [
                        '#22c55e', // Yeşil
                        '#ef4444'  // Kırmızı
                    ],
                    borderColor: '#1e293b',
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { 
                            color: '#e2e8f0',
                            font: { size: 14 },
                            padding: 20
                        }
                    },
                    title: {
                        display: true,
                        text: '📊 Gerçek Zamanlı Durum Analizi',
                        color: '#e2e8f0',
                        font: { size: 18, weight: 'bold' },
                        padding: { bottom: 20 }
                    }
                }
            }
        });

        // Veri Güncelleme
        setInterval(function() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                var alarmBox = document.getElementById("alarm-box");
                var videoWrapper = document.getElementById("video-border");
                
                // Alarm Kontrol
                if (data.alarm) {
                    alarmBox.style.display = "block";
                    videoWrapper.style.borderColor = "var(--danger-color)";
                    videoWrapper.style.boxShadow = "0 0 30px rgba(239, 68, 68, 0.4)";
                } else {
                    alarmBox.style.display = "none";
                    videoWrapper.style.borderColor = "var(--border-color)";
                    videoWrapper.style.boxShadow = "0 10px 15px -3px rgba(0, 0, 0, 0.5)";
                }

                // GRAFİK GÜNCELLEME
                if(data.safe_count + data.violation_count > 0){
                     myChart.data.datasets[0].data = [data.safe_count, data.violation_count];
                } else {
                     // Eğer veri sıfırlanmışsa grafiği de sıfırla
                     myChart.data.datasets[0].data = [1, 0]; // 1 tane sembolik yeşil koy
                }
                myChart.update();
            });
        }, 500);

        // İSTATİSTİK SIFIRLAMA FONKSİYONU
        function resetStats() {
            fetch('/reset_stats', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log("İstatistikler sıfırlandı!");
                // Grafiği görsel olarak hemen temizle
                myChart.data.datasets[0].data = [1, 0]; 
                myChart.update();
            });
        }
    </script>
</body>
</html>
"""

# ================= FONKSİYONLAR =================

def process_frame(img_bytes):
    global global_frame, alarm_status, total_safe, total_violation
    
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    try:
        results = model.predict(frame, confidence=40).json()
        predictions = results['predictions']
    except:
        predictions = []

    violation_detected = False

    for det in predictions:
        x, y, w, h = int(det['x']), int(det['y']), int(det['width']), int(det['height'])
        label = det['class']
        
        start_point = (int(x - w/2), int(y - h/2))
        end_point = (int(x + w/2), int(y + h/2))

        color = (0, 255, 0) 
        
        if label.startswith("NO-") or label in ["no_helmet", "no_vest", "NO-Hardhat", "NO-Safety Vest"]:
            color = (0, 0, 255) # Kırmızı
            violation_detected = True

        cv2.rectangle(frame, start_point, end_point, color, 2)
        cv2.putText(frame, label, (start_point[0], start_point[1]-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    if violation_detected:
        total_violation += 1
    else:
        if len(predictions) > 0: 
            total_safe += 1

    alarm_status = violation_detected
    
    ret, buffer = cv2.imencode('.jpg', frame)
    global_frame = buffer.tobytes()
    
    return violation_detected

# ================= WEB ROTLARI =================

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        is_violation = process_frame(request.data)
        command = "on" if is_violation else "off"
        return jsonify({"command": command})
    except Exception as e:
        print(e)
        return jsonify({"status": "error"}), 500

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            if global_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + global_frame + b'\r\n')
            time.sleep(0.1)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify({
        "alarm": alarm_status,
        "safe_count": total_safe,
        "violation_count": total_violation
    })


@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    global total_safe, total_violation
    total_safe = 0
    total_violation = 0
    return jsonify({"status": "reset"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
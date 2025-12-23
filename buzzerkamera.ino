#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// ================= WIFI AYARLARI =================
const char* ssid = "Ronahi";
const char* password = "Ronahi12";

// ================= PINLER =================
#define LED_PIN 2        // HARİCİ LED
#define BUZZER_PIN 4     // AKTİF BUZZER (FLASH LED PIN)

// ================= KAMERA PINLERİ (AI THINKER) =================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

httpd_handle_t server = NULL;

// ================= KOMUT HANDLER =================
static esp_err_t control_handler(httpd_req_t *req) {
  char buf[50];

  if (httpd_req_get_url_query_str(req, buf, sizeof(buf)) == ESP_OK) {

    if (strstr(buf, "alert=on")) {
  digitalWrite(LED_PIN, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
  Serial.println("ALARM ACILDI!");
  delay(10);
}
if (strstr(buf, "alert=off")) {
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.println("ALARM KAPANDI!");
  delay(10);
}

  }

  httpd_resp_send(req, "OK", HTTPD_RESP_USE_STRLEN);
  return ESP_OK;
}

// ================= VIDEO STREAM =================
static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t * fb;
  httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) continue;

    httpd_resp_send_chunk(req, "--frame\r\n", 9);
    httpd_resp_send_chunk(req, "Content-Type: image/jpeg\r\n\r\n", 31);
    httpd_resp_send_chunk(req, (char*)fb->buf, fb->len);
    httpd_resp_send_chunk(req, "\r\n", 2);

    esp_camera_fb_return(fb);
  }
}

// ================= SERVER =================
void startServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();

  httpd_uri_t stream_uri = {
    .uri = "/stream",
    .method = HTTP_GET,
    .handler = stream_handler
  };

  httpd_uri_t control_uri = {
    .uri = "/control",
    .method = HTTP_GET,
    .handler = control_handler
  };

  httpd_start(&server, &config);
  httpd_register_uri_handler(server, &stream_uri);
  httpd_register_uri_handler(server, &control_uri);
}

// ================= SETUP =================
void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); 

  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // ⚠️ BAŞLANGIÇTA MUTLAKA KAPALI OLSUN
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = 2;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("❌ Kamera baslatilamadi");
    return;
  }

  WiFi.begin(ssid, password);
  Serial.print("WiFi baglaniyor");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Baglandi!");
  Serial.print("📷 Kamera Linki: http://");
  Serial.print(WiFi.localIP());
  Serial.println("/stream");

  startServer();
}

void loop() {
  delay(10000);
}

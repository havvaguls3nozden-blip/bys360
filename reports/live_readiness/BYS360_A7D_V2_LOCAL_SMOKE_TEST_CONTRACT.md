# BYS360 Aşama 7D Local Smoke Test Sözleşmesi

Tarih: 2026-06-12T13:50:31

## Özet

- OK: False
- HTTP modu: False
- Base URL: ``
- Passed: 7
- Warnings: 0
- Failed: 2

## Smoke Kalemleri

### PASS — Ana sayfa / giriş yönlendirme
- Yol: `/`
- Seviye: high
- Contract OK: True
- Kanıt yolları bulundu: True
- Terim eşleşmeleri: ['@main', 'route("/"', 'index']
- Dosya kanıtları: ['app/__init__.py', 'app/main_handlers', 'app/routes.py']

### PASS — Login
- Yol: `/login`
- Seviye: high
- Contract OK: True
- Kanıt yolları bulundu: True
- Terim eşleşmeleri: ['login', 'auth']
- Dosya kanıtları: ['app/auth', 'app/templates']

### PASS — Dashboard
- Yol: `/dashboard`
- Seviye: high
- Contract OK: True
- Kanıt yolları bulundu: True
- Terim eşleşmeleri: ['dashboard']
- Dosya kanıtları: ['app/dashboard', 'app/templates/dashboard']

### PASS — Portal
- Yol: `/portal`
- Seviye: medium
- Contract OK: True
- Kanıt yolları bulundu: True
- Terim eşleşmeleri: ['portal']
- Dosya kanıtları: ['app/portal', 'app/templates/portal']

### PASS — Geri Bildirim
- Yol: `/feedback/gonder`
- Seviye: medium
- Contract OK: True
- Kanıt yolları bulundu: True
- Terim eşleşmeleri: ['feedback', 'gonder', 'geri']
- Dosya kanıtları: ['app', 'app/communication', 'app/support', 'app/templates/feedback']

### FAIL — 404 hata şablonu
- Yol: `/__bys360_missing_smoke_page__`
- Seviye: medium
- Contract OK: False
- Kanıt yolları bulundu: True
- Terim eşleşmeleri: []
- Dosya kanıtları: ['app/templates/errors/404.html']

### FAIL — 500 hata şablonu
- Yol: `/__bys360_500_template_check__`
- Seviye: medium
- Contract OK: False
- Kanıt yolları bulundu: True
- Terim eşleşmeleri: []
- Dosya kanıtları: ['app/templates/errors/500.html']

### PASS — Static CSS
- Yol: `/static/css`
- Seviye: low
- Contract OK: True
- Kanıt yolları bulundu: True
- Terim eşleşmeleri: ['.css']
- Dosya kanıtları: ['app/static/css']

### PASS — Mobil API kökü
- Yol: `/api/mobile`
- Seviye: medium
- Contract OK: True
- Kanıt yolları bulundu: True
- Terim eşleşmeleri: ['mobile_api_bp', 'api/mobile', 'mobile']
- Dosya kanıtları: ['app/api/mobile']

## Karar

A7D sonucu: Kritik/orta seviye smoke kalemlerinde eksik var; canlı öncesi tamamlanmalı.
# BYS360 10/10 Red Gate V1 Overlay

Bu overlay ilk kırmızı güvenlik ve paket hijyeni kapısını kapatmak için hazırlandı.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_10_10_RED_GATE_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_10_10_red_gate_v1.ps1 -ProjectRoot "C:\bys360\project"
```

CI workflow genişletmesini şimdilik istemezsen:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_10_10_red_gate_v1.ps1 -ProjectRoot "C:\bys360\project" -NoCi
```

## Kapsam

- `post.body|safe` kaldırılır.
- Sosyal embed için `safe_social_embed` filtresi eklenir.
- `attrs|safe` yerine kontrollü `safe_nav_attrs` filtresi kullanılır.
- Kurumsal Bilgilendirme Merkezi `join('<br>')|safe` kaldırılır.
- SECRET_KEY bloğu sadeleşir.
- Paket şişiren klasörler `.gitignore` içine güçlendirilmiş olarak eklenir.
- XSS regresyon testi eklenir.

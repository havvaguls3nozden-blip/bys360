BYS360 Mobile V2.8.77 Android V2 Embedding PowerShell 5.1 Fix Overlay

Bu overlay, V2.8.76 scriptindeki PowerShell uyumluluk hatasını düzeltir.
Özellikle Windows PowerShell 5.1'de çalışmayan parantez içi if kullanımını kaldırır.

Uygulama:
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_Mobile_V2_8_77_Android_V2_Embedding_PS51_Fix_Overlay.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\repair_bys360_mobile_v2_8_77_android_v2_embedding_ps51_fix.ps1 -ProjectRoot "C:\bys360\project"

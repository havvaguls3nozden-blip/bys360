# BYS360 iOS Build Notu — V2.8.72

Bu overlay App Store öncesi kritik güvenlik düzeltmesini yapar: `NSAllowsArbitraryLoads` kaldırıldı, canlı BYS360 alan adı HTTPS istisnası olarak bırakıldı.

## iOS proje dosyaları eksikse

Flutter projesi içinde `ios/Runner.xcodeproj` ve `ios/Runner.xcworkspace` yoksa bunlar zip'e elle yazılmamalı; Flutter tarafından yeniden üretilmelidir.

Mac veya macOS cloud runner üzerinde:

```bash
cd mobile_flutter/bys360_mobile_native
flutter clean
flutter pub get
flutter create --platforms=ios .
cd ios
pod install
```

Sonra build:

```bash
cd ..
flutter build ipa --release \
  --dart-define=BYS360_APP_ENV=prod \
  --dart-define=BYS360_API_BASE=https://bys360.canakkaletarihialan.gov.tr
```

Apple Developer hesabı olmadan App Store IPA imzalama tamamlanmaz. Mac yoksa Codemagic veya GitHub Actions macOS runner kullanılmalıdır.

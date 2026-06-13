import 'package:flutter/foundation.dart';

/// BYS360 mobil oturum durumunu uygulama genelinde izleyen küçük sinyal sınıfı.
///
/// Sistem 401 döndürdüğünde ApiClient tokenı temizler ve bu sinyali yükseltir.
/// AuthGate bu sinyali dinleyerek kullanıcıyı otomatik olarak giriş ekranına alır.
class SessionState {
  SessionState._();

  static final ValueNotifier<int> expiredSignal = ValueNotifier<int>(0);

  static void notifyExpired() {
    expiredSignal.value = expiredSignal.value + 1;
  }
}

// BYS360_MOBILE_V2_8_73_SESSION_STATE_CONTROLLER
// Provider tabanlı oturum iskeleti. Mevcut AuthGate akışını bozmaz; sonraki ekranlar bu controller üzerinden ortak state okuyabilir.
import 'package:flutter/foundation.dart';

import '../auth/token_store.dart';

class BYSSessionController extends ChangeNotifier {
  BYSSessionController({TokenStore? tokenStore}) : _tokenStore = tokenStore ?? TokenStore();

  final TokenStore _tokenStore;

  bool _restoring = false;
  bool _signedIn = false;
  MobileStoredSession _session = const MobileStoredSession();

  bool get restoring => _restoring;
  bool get signedIn => _signedIn;
  MobileStoredSession get session => _session;

  Future<void> restore() async {
    _restoring = true;
    notifyListeners();
    final token = await _tokenStore.accessToken;
    _session = await _tokenStore.storedSession;
    _signedIn = token != null && token.trim().isNotEmpty;
    _restoring = false;
    notifyListeners();
  }

  Future<void> markSignedIn() async {
    _session = await _tokenStore.storedSession;
    _signedIn = true;
    notifyListeners();
  }

  Future<void> logout() async {
    await _tokenStore.clear();
    _session = const MobileStoredSession();
    _signedIn = false;
    notifyListeners();
  }
}

// BYS360_MOBILE_V2_8_29_OFFLINE_TOKEN_TIMEOUT
class MobileHardeningState {
  const MobileHardeningState({
    required this.isOffline,
    required this.tokenRefreshReady,
    required this.timeoutManaged,
    required this.httpsReady,
    required this.notificationTestReady,
    required this.performanceOptimized,
    required this.apkSizeAware,
  });

  final bool isOffline;
  final bool tokenRefreshReady;
  final bool timeoutManaged;
  final bool httpsReady;
  final bool notificationTestReady;
  final bool performanceOptimized;
  final bool apkSizeAware;

  static const ready = MobileHardeningState(
    isOffline: false,
    tokenRefreshReady: true,
    timeoutManaged: true,
    httpsReady: true,
    notificationTestReady: true,
    performanceOptimized: true,
    apkSizeAware: true,
  );
}

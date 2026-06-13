// BYS360_MOBILE_PORTAL_NATIVE_WEBVIEW_V2_8_84
// APK icindeki Kurumsal Portal artik sahte kart ekranı degil;
// web uygulamasindaki gercek /portal/ sayfasini mobil uyumlu WebView olarak acar.

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'core/auth/token_store.dart';
import 'core/config/app_config.dart';

const Color _bys360Red = Color(0xFF8B0000);
const Color _bys360DeepRed = Color(0xFF650000);
const Color _bys360SoftBg = Color(0xFFF7F4F1);
const Color _bys360Surface = Color(0xFFFFFFFF);
const Color _bys360SoftRed = Color(0xFFF7E9E7);
const Color _bys360Border = Color(0xFFE8DCDC);
const Color _bys360Ink = Color(0xFF241A17);
const Color _bys360Muted = Color(0xFF6B5F5A);

class Bys360PortalRoutes {
  static const String home = '/portal/';
  static const String feed = '/portal/';
  static const String people = '/portal/people';
  static const String posts = '/portal/';
  static const String profileMe = '/portal/profile/me';
  static const String support = '/support';
  static const String assistant = '/assistant';
}

class Bys360PortalHomeEntryCard extends StatelessWidget {
  const Bys360PortalHomeEntryCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      margin: const EdgeInsets.symmetric(vertical: 8),
      color: _bys360Surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(24),
        side: const BorderSide(color: _bys360Border),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute<void>(builder: (_) => const Bys360PortalHomeScreen()),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(colors: [_bys360Red, _bys360DeepRed]),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: const Icon(Icons.public, color: Colors.white, size: 27),
              ),
              const SizedBox(width: 14),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Kurumsal Portal',
                      style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: _bys360Ink),
                    ),
                    SizedBox(height: 5),
                    Text(
                      'Web uygulamasındaki gerçek portal ekranını mobil uyumlu açar.',
                      style: TextStyle(fontSize: 13.5, height: 1.35, color: _bys360Muted),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.chevron_right, color: _bys360Red),
            ],
          ),
        ),
      ),
    );
  }
}

class Bys360PortalDrawerTile extends StatelessWidget {
  const Bys360PortalDrawerTile({super.key});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(color: _bys360SoftRed, borderRadius: BorderRadius.circular(14)),
        child: const Icon(Icons.public, color: _bys360Red, size: 21),
      ),
      title: const Text('Kurumsal Portal', style: TextStyle(fontWeight: FontWeight.w900)),
      subtitle: const Text('Webdeki gerçek portal', maxLines: 1, overflow: TextOverflow.ellipsis),
      onTap: () {
        final navigator = Navigator.of(context);
        if (navigator.canPop()) navigator.pop();
        navigator.push(MaterialPageRoute<void>(builder: (_) => const Bys360PortalHomeScreen()));
      },
    );
  }
}

class Bys360PortalHomeScreen extends StatefulWidget {
  const Bys360PortalHomeScreen({super.key, this.initialPath = Bys360PortalRoutes.home});

  final String initialPath;

  @override
  State<Bys360PortalHomeScreen> createState() => _Bys360PortalHomeScreenState();
}

class _Bys360PortalHomeScreenState extends State<Bys360PortalHomeScreen> {
  final TokenStore _tokenStore = TokenStore();
  WebViewController? _controller;
  int _progress = 0;
  bool _hasError = false;
  String _errorMessage = '';

  @override
  void initState() {
    super.initState();
    unawaited(_initPortal());
  }

  Future<void> _initPortal() async {
    final token = await _tokenStore.accessToken;
    final uri = AppConfig.uri(widget.initialPath);
    final headers = <String, String>{
      'X-Requested-With': 'BYS360-Mobile',
      if (token != null && token.trim().isNotEmpty) 'Authorization': 'Bearer ${token.trim()}',
    };

    final controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(_bys360SoftBg)
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (value) {
            if (!mounted) return;
            setState(() => _progress = value);
          },
          onPageStarted: (_) {
            if (!mounted) return;
            setState(() {
              _hasError = false;
              _errorMessage = '';
            });
          },
          onPageFinished: (_) async {
            await _applyMobileViewport();
            if (!mounted) return;
            setState(() => _progress = 100);
          },
          onWebResourceError: (error) {
            if (!mounted) return;
            setState(() {
              _hasError = true;
              _errorMessage = 'Portal ekranı şu anda yüklenemedi. İnternet bağlantınızı ve BYS360 erişimini kontrol edip tekrar deneyin.';
            });
          },
        ),
      )
      ..loadRequest(uri, headers: headers);

    if (!mounted) return;
    setState(() => _controller = controller);
  }

  Future<void> _applyMobileViewport() async {
    final controller = _controller;
    if (controller == null) return;
    const script = """
(function() {
  var meta = document.querySelector('meta[name=viewport]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.name = 'viewport';
    document.head.appendChild(meta);
  }
  meta.content = 'width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover';
  document.documentElement.style.maxWidth = '100%';
  document.documentElement.style.overflowX = 'hidden';
  document.body.style.maxWidth = '100%';
  document.body.style.overflowX = 'hidden';
  document.body.style.background = '#F7F4F1';
  var wide = document.querySelectorAll('table, img, video, iframe, .container, .row, .card, main, section');
  wide.forEach(function(el) {
    el.style.maxWidth = '100%';
    el.style.boxSizing = 'border-box';
  });
})();
""";
    try {
      await controller.runJavaScript(script);
    } catch (_) {
      // Portal tarafinda CSP engeli olursa ekran yine normal sekilde yuklenmeye devam eder.
    }
  }

  Future<void> _reload() async {
    final controller = _controller;
    if (controller == null) {
      await _initPortal();
      return;
    }
    await controller.reload();
  }

  Future<void> _goHome() async {
    final controller = _controller;
    if (controller == null) return;
    final token = await _tokenStore.accessToken;
    await controller.loadRequest(
      AppConfig.uri(Bys360PortalRoutes.home),
      headers: <String, String>{
        'X-Requested-With': 'BYS360-Mobile',
        if (token != null && token.trim().isNotEmpty) 'Authorization': 'Bearer ${token.trim()}',
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        if (controller != null && await controller.canGoBack()) {
          await controller.goBack();
          return;
        }
        if (context.mounted) {
          Navigator.of(context).maybePop();
        }
      },
      child: Scaffold(
        backgroundColor: _bys360SoftBg,
        appBar: AppBar(
          backgroundColor: _bys360Red,
          foregroundColor: Colors.white,
          elevation: 0,
          title: const Text('Kurumsal Portal', style: TextStyle(fontWeight: FontWeight.w900)),
          actions: [
            IconButton(
              tooltip: 'Portal ana sayfası',
              onPressed: _goHome,
              icon: const Icon(Icons.home_outlined),
            ),
            IconButton(
              tooltip: 'Yenile',
              onPressed: _reload,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
        body: SafeArea(
          child: Stack(
            children: [
              if (controller == null)
                const _PortalLoadingState()
              else if (_hasError)
                _PortalErrorState(message: _errorMessage, onRetry: _reload)
              else
                WebViewWidget(controller: controller),
              if (_progress > 0 && _progress < 100)
                Align(
                  alignment: Alignment.topCenter,
                  child: LinearProgressIndicator(
                    value: _progress / 100,
                    minHeight: 3,
                    backgroundColor: _bys360SoftRed,
                    color: _bys360Red,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PortalLoadingState extends StatelessWidget {
  const _PortalLoadingState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(color: _bys360Red),
          SizedBox(height: 14),
          Text('Kurumsal portal yükleniyor...', style: TextStyle(color: _bys360Muted, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _PortalErrorState extends StatelessWidget {
  const _PortalErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: _bys360Surface,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: _bys360Border),
            boxShadow: [BoxShadow(blurRadius: 24, offset: const Offset(0, 10), color: Colors.black.withValues(alpha: .05))],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 58,
                height: 58,
                decoration: BoxDecoration(color: _bys360SoftRed, borderRadius: BorderRadius.circular(20)),
                child: const Icon(Icons.public_off_outlined, color: _bys360Red),
              ),
              const SizedBox(height: 14),
              const Text('Portal açılamadı', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: _bys360Ink)),
              const SizedBox(height: 8),
              Text(message, textAlign: TextAlign.center, style: const TextStyle(color: _bys360Muted, height: 1.35)),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Tekrar Dene'),
                style: ElevatedButton.styleFrom(backgroundColor: _bys360Red, foregroundColor: Colors.white),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

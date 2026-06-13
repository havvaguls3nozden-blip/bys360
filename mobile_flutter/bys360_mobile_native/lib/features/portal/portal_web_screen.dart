// BYS360_MOBILE_PORTAL_FEEDBACK_V2_8_87
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../../core/config/app_config.dart';
import '../../core/theme/app_theme.dart';

class PortalWebScreen extends StatefulWidget {
  const PortalWebScreen({
    super.key,
    String? title,
    String? subtitle,
    String? initialPath,
    String? moduleTitle,
    String? moduleSubtitle,
    String? modulePath,
  })  : moduleTitle = moduleTitle ?? title ?? 'Kurumsal Portal',
        moduleSubtitle = moduleSubtitle ?? subtitle ?? 'BYS360 web portal alanı mobil uyumlu görünümle açılır.',
        modulePath = modulePath ?? initialPath ?? '/portal';

  final String moduleTitle;
  final String moduleSubtitle;
  final String modulePath;

  @override
  State<PortalWebScreen> createState() => _PortalWebScreenState();
}

class _PortalWebScreenState extends State<PortalWebScreen> {
  late final WebViewController _controller;
  var _loading = true;
  var _hasError = false;
  String? _errorText;

  Uri get _targetUri => AppConfig.uri(widget.modulePath);

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(BYS360Colors.pageBackground)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) => setState(() {
            _loading = true;
            _hasError = false;
            _errorText = null;
          }),
          onPageFinished: (_) async {
            await _injectMobileViewportGuard();
            if (mounted) setState(() => _loading = false);
          },
          onWebResourceError: (_) => setState(() {
            _loading = false;
            _hasError = true;
            _errorText = '${widget.moduleTitle} şu anda yüklenemedi. Bağlantıyı kontrol edip tekrar deneyin.';
          }),
        ),
      )
      ..loadRequest(_targetUri);
  }

  Future<void> _injectMobileViewportGuard() async {
    const script = """
(function(){
  var viewport = document.querySelector('meta[name="viewport"]');
  if(!viewport){ viewport = document.createElement('meta'); viewport.name = 'viewport'; document.head.appendChild(viewport); }
  viewport.content = 'width=device-width, initial-scale=1, viewport-fit=cover';
  document.documentElement.style.maxWidth = '100%';
  document.documentElement.style.overflowX = 'hidden';
  document.body.style.maxWidth = '100%';
  document.body.style.overflowX = 'hidden';
  var style = document.getElementById('bys360-mobile-portal-app-guard');
  if(!style){
    style = document.createElement('style');
    style.id = 'bys360-mobile-portal-app-guard';
    style.innerHTML = '*{box-sizing:border-box!important} body{margin:0!important} img,video,iframe{max-width:100%!important;height:auto!important} table{max-width:100%!important} .container,.content,.main,.portal-layout,.portal-shell,.portal-grid,.portal-content,.portal-main,.portal-sidebar{max-width:100%!important;min-width:0!important} @media(max-width:820px){.portal-layout,.portal-grid,.portal-shell,.row{display:block!important}.portal-sidebar,.portal-right,.right-panel,.desktop-only{display:none!important}.portal-card,.post-card,.composer-card,.card{width:100%!important;margin-left:0!important;margin-right:0!important}.col,.col-md-4,.col-md-8,.col-lg-3,.col-lg-9{width:100%!important;max-width:100%!important;flex:0 0 100%!important}}';
    document.head.appendChild(style);
  }
})();
""";
    try { await _controller.runJavaScript(script); } catch (_) {}
  }

  Future<void> _reload() async {
    setState(() {
      _loading = true;
      _hasError = false;
      _errorText = null;
    });
    await _controller.loadRequest(_targetUri);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _ModuleHeader(
          title: widget.moduleTitle,
          subtitle: widget.moduleSubtitle,
          onReload: _reload,
        ),
        Expanded(
          child: ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(18)),
            child: Stack(
              children: [
                Positioned.fill(child: WebViewWidget(controller: _controller)),
                if (_loading)
                  const Positioned.fill(
                    child: ColoredBox(
                      color: BYS360Colors.pageBackground,
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  ),
                if (_hasError)
                  Positioned.fill(
                    child: ColoredBox(
                      color: BYS360Colors.pageBackground,
                      child: Center(
                        child: Padding(
                          padding: const EdgeInsets.all(22),
                          child: Card(
                            child: Padding(
                              padding: const EdgeInsets.all(20),
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.public_off_outlined, color: BYS360Colors.corporateRed, size: 42),
                                  const SizedBox(height: 12),
                                  Text(widget.moduleTitle, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
                                  const SizedBox(height: 8),
                                  Text(_errorText ?? 'Lütfen tekrar deneyin.', textAlign: TextAlign.center, style: const TextStyle(color: BYS360Colors.mutedText)),
                                  const SizedBox(height: 16),
                                  ElevatedButton.icon(onPressed: _reload, icon: const Icon(Icons.refresh), label: const Text('Tekrar Dene')),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _ModuleHeader extends StatelessWidget {
  const _ModuleHeader({required this.title, required this.subtitle, required this.onReload});

  final String title;
  final String subtitle;
  final VoidCallback onReload;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(12, 12, 12, 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(BYS360Radii.lg),
        border: Border.all(color: BYS360Colors.cardBorder),
        boxShadow: BYS360Shadows.card,
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(15)),
            child: const Icon(Icons.public_outlined, color: BYS360Colors.corporateRed),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900), maxLines: 1, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 3),
                Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: BYS360Colors.mutedText), maxLines: 2, overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          IconButton(onPressed: onReload, icon: const Icon(Icons.refresh, color: BYS360Colors.corporateRed), tooltip: 'Yenile'),
        ],
      ),
    );
  }
}

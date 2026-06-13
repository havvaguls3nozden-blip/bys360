// BYS360_MOBILE_V2_8_73_GO_ROUTER_SHELL
// Mevcut AuthGate + MobileShell akışını bozmadan go_router ana omurgası kurulur.
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/login_screen.dart';
import '../../features/profile/profile_screen.dart';
import '../auth/auth_gate.dart';
import '../network/api_client.dart';
import '../theme/app_theme.dart';
import 'bys360_route_names.dart';

class BYS360AppRouter {
  BYS360AppRouter._();

  static final GoRouter router = GoRouter(
    initialLocation: BYS360RoutePaths.root,
    debugLogDiagnostics: false,
    routes: <RouteBase>[
      GoRoute(
        path: BYS360RoutePaths.root,
        name: BYS360RouteNames.root,
        builder: (context, state) => const AuthGate(),
      ),
      // Bu rotalar kademeli geçiş için hazır tutulur. Mevcut akış AuthGate içinde korunur.
      GoRoute(
        path: BYS360RoutePaths.login,
        name: BYS360RouteNames.login,
        builder: (context, state) => LoginScreen(onLoginSuccess: () => context.go(BYS360RoutePaths.root)),
      ),
      GoRoute(
        path: BYS360RoutePaths.profile,
        name: BYS360RouteNames.profile,
        builder: (context, state) => ProfileScreen(apiClient: ApiClient()),
      ),
    ],
    errorBuilder: (context, state) => const BYS360RouteErrorScreen(),
  );
}

class BYS360RouteErrorScreen extends StatelessWidget {
  const BYS360RouteErrorScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: BYS360Colors.pageBackground,
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(22),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 58,
                      height: 58,
                      decoration: BoxDecoration(
                        color: BYS360Colors.softRed,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Icon(Icons.route_outlined, color: BYS360Colors.corporateRed),
                    ),
                    const SizedBox(height: 14),
                    Text(
                      'Bu sayfaya şu anda ulaşılamadı',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Menüden ilgili ekrana yeniden geçebilir veya ana sayfaya dönebilirsiniz.',
                      style: TextStyle(color: BYS360Colors.mutedText, height: 1.35),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed: () => context.go(BYS360RoutePaths.root),
                      icon: const Icon(Icons.home_outlined),
                      label: const Text('Ana Sayfaya Dön'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

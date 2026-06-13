import 'package:flutter/material.dart';

import '../../features/auth/login_screen.dart';
import '../../features/shell/mobile_shell.dart';
import '../widgets/bys360_logo.dart';
import 'auth_controller.dart';
import 'session_state.dart';
import 'token_store.dart';

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  final TokenStore _tokenStore = TokenStore();
  final AuthController _authController = AuthController();
  bool _checking = true;
  bool _signedIn = false;

  @override
  void initState() {
    super.initState();
    SessionState.expiredSignal.addListener(_handleSessionExpired);
    _load();
  }

  @override
  void dispose() {
    SessionState.expiredSignal.removeListener(_handleSessionExpired);
    super.dispose();
  }

  Future<void> _load() async {
    final token = await _tokenStore.accessToken;
    if (!mounted) return;
    setState(() {
      _signedIn = token != null && token.isNotEmpty;
      _checking = false;
    });
  }

  void _handleSessionExpired() {
    if (!mounted) return;
    setState(() {
      _signedIn = false;
      _checking = false;
    });
  }

  Future<void> _logout() async {
    await _authController.logout();
    if (!mounted) return;
    setState(() => _signedIn = false);
  }

  void _markSignedIn() => setState(() => _signedIn = true);

  @override
  Widget build(BuildContext context) {
    if (_checking) {
      return const Scaffold(
        body: Center(
          child: SizedBox(width: 210, child: BYS360Logo()),
        ),
      );
    }
    if (_signedIn) return MobileShell(onLogout: _logout);
    return LoginScreen(onLoginSuccess: _markSignedIn);
  }
}

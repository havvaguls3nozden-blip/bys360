import 'package:flutter/material.dart';

import '../../core/auth/auth_controller.dart';
import '../../core/config/app_config.dart';
import '../../core/network/api_exception.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/bys360_copy.dart';
import '../../core/widgets/bys360_logo.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.onLoginSuccess});

  final VoidCallback onLoginSuccess;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _auth = AuthController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _loading = false;
  bool _obscure = true;
  String? _error;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await _auth.login(_usernameController.text, _passwordController.text);
      if (mounted) widget.onLoginSuccess();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error is ApiException ? BYS360Copy.error(error.message) : BYS360Copy.error(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _demoLogin() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await _auth.demoLogin();
      if (mounted) widget.onLoginSuccess();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = BYS360Copy.error(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [BYS360Colors.pageBackgroundWarm, BYS360Colors.pageBackground],
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(22, 22, 22, 30),
            children: [
              const SizedBox(height: 10),
              Center(
                child: Container(
                  width: double.infinity,
                  constraints: const BoxConstraints(maxWidth: 440),
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(32),
                    border: Border.all(color: BYS360Colors.cardBorder),
                    boxShadow: BYS360Shadows.elevated,
                  ),
                  child: const BYS360Logo(height: 178),
                ),
              ),
              const SizedBox(height: 22),
              Text('BYS360 Mobile', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w900), textAlign: TextAlign.center),
              const SizedBox(height: 8),
              const Text(
                'Bütünleşik Yönetim Sistemi mobil giriş ekranı. Yetkili kullanıcılar kurumsal süreçlere güvenli şekilde erişir.',
                textAlign: TextAlign.center,
                style: TextStyle(color: BYS360Colors.mutedText, height: 1.35),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _usernameController,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(prefixIcon: Icon(Icons.person_outline), labelText: 'Kullanıcı adı / sicil'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _passwordController,
                obscureText: _obscure,
                onSubmitted: (_) => _login(),
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.lock_outline),
                  labelText: 'Şifre',
                  suffixIcon: IconButton(onPressed: () => setState(() => _obscure = !_obscure), icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined)),
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(13),
                  decoration: BoxDecoration(
                    color: BYS360Colors.softRed,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: BYS360Colors.corporateRed.withValues(alpha: .12)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.info_outline, color: BYS360Colors.corporateRed, size: 20),
                      const SizedBox(width: 9),
                      Expanded(child: Text(_error!, style: const TextStyle(color: BYS360Colors.corporateRed, fontWeight: FontWeight.w800, height: 1.30))),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 18),
              ElevatedButton.icon(
                onPressed: _loading ? null : _login,
                icon: _loading ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.login),
                label: const Text('Giriş Yap'),
              ),
              if (AppConfig.demoFallback) ...[
                const SizedBox(height: 10),
                OutlinedButton.icon(onPressed: _loading ? null : _demoLogin, icon: const Icon(Icons.mobile_friendly), label: const Text('Ön İzleme')),
              ],
              const SizedBox(height: 20),
              const _LoginInfo(),
            ],
          ),
        ),
      ),
    );
  }
}

class _LoginInfo extends StatelessWidget {
  const _LoginInfo();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(color: BYS360Colors.softRed, borderRadius: BorderRadius.circular(15)),
              child: const Icon(Icons.shield_outlined, color: BYS360Colors.corporateRed),
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Text(
                'Mobil uygulama yetki kontrollü çalışır. Yetki dışı veri, puan, görüş ve hassas içerik mobilde gösterilmez.',
                style: TextStyle(color: BYS360Colors.mutedText, height: 1.35),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

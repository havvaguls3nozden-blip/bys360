import 'package:flutter/material.dart';

import '../../core/api/mobile_real_api_contract.dart';
import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/module_api_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key, required this.apiClient});

  final ApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return ModuleApiScreen(
      apiClient: apiClient,
      path: MobileRealApiContract.profile,
      title: 'Hesabım',
      subtitle: 'Mobil oturum, rol ve kullanıcı bilgileri.',
      badge: 'Profil',
      icon: Icons.account_circle_outlined,
      tone: BYS360Colors.corporateRed,
    );
  }
}

// BYS360_MOBILE_V2_8_25_REAL_API_P0 profil gerçek API sözleşmesi

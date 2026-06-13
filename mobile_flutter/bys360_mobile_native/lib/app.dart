// BYS360_MOBILE_V2_8_73_APP_ROUTER_PROVIDER
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/navigation/bys360_app_router.dart';
import 'core/state/bys_session_controller.dart';
import 'core/theme/app_theme.dart';

class BYS360MobileApp extends StatelessWidget {
  const BYS360MobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => BYSSessionController()..restore(),
      child: MaterialApp.router(
        debugShowCheckedModeBanner: false,
        title: 'BYS360 Mobile',
        theme: BYS360Theme.light,
        darkTheme: BYS360Theme.light,
        themeMode: ThemeMode.light,
        routerConfig: BYS360AppRouter.router,
      ),
    );
  }
}

// BYS360_MOBILE_V2_8_75_APP_MATURITY_P1_APP_THEME_MODE

// BYS360_MOBILE_PORTAL_LIGHT_HOME_V2_8_81_FORCE_LIGHT_THEME

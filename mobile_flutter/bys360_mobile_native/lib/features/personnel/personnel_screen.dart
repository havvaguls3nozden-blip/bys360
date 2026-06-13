import 'package:flutter/material.dart';

import 'personnel_mobile_p1_screen.dart';

class PersonnelScreen extends StatelessWidget {
  const PersonnelScreen({super.key, this.apiClient});

  final dynamic apiClient;

  @override
  Widget build(BuildContext context) {
    return PersonnelMobileP1Screen(apiClient: apiClient);
  }
}

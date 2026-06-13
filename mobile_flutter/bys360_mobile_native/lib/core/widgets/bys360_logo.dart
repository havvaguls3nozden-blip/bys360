import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

const String kBYS360LogoAsset = 'assets/images/bys360_logo.png';
const String kBYS360LauncherIconAsset = 'assets/images/bys360_app_icon.png';

class BYS360Logo extends StatelessWidget {
  const BYS360Logo({
    super.key,
    this.width,
    this.height,
    this.fit = BoxFit.contain,
    this.semanticLabel = 'BYS360 Bütünleşik Yönetim Sistemi logosu',
  });

  final double? width;
  final double? height;
  final BoxFit fit;
  final String semanticLabel;

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      kBYS360LogoAsset,
      width: width,
      height: height,
      fit: fit,
      semanticLabel: semanticLabel,
      filterQuality: FilterQuality.high,
      errorBuilder: (context, error, stackTrace) => _LogoFallback(width: width, height: height),
    );
  }
}

class BYS360AppIcon extends StatelessWidget {
  const BYS360AppIcon({
    super.key,
    this.size = 42,
    this.width,
    this.height,
    this.borderRadius = 14,
  });

  final double size;
  final double? width;
  final double? height;
  final double borderRadius;

  @override
  Widget build(BuildContext context) {
    final iconWidth = width ?? size;
    final iconHeight = height ?? size;

    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: Container(
        width: iconWidth,
        height: iconHeight,
        padding: const EdgeInsets.all(3),
        color: Colors.white,
        alignment: Alignment.center,
        child: Image.asset(
          kBYS360LogoAsset,
          width: iconWidth,
          height: iconHeight,
          fit: BoxFit.contain,
          semanticLabel: 'BYS360 mobil logo',
          filterQuality: FilterQuality.high,
          errorBuilder: (context, error, stackTrace) => Container(
            width: iconWidth,
            height: iconHeight,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: BYS360Colors.corporateRed,
              borderRadius: BorderRadius.circular(borderRadius),
            ),
            child: const Text('BYS360', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 10)),
          ),
        ),
      ),
    );
  }
}

class _LogoFallback extends StatelessWidget {
  const _LogoFallback({this.width, this.height});

  final double? width;
  final double? height;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: BYS360Colors.cardBorder),
      ),
      child: const Text('BYS360', style: TextStyle(color: BYS360Colors.corporateRed, fontWeight: FontWeight.w900)),
    );
  }
}

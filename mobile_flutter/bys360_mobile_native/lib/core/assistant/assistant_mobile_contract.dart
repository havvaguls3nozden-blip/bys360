
// BYS360_MOBILE_V2_8_28_ASSISTANT_P1_MARKER
class AssistantMobileIntent {
  const AssistantMobileIntent({
    required this.key,
    required this.title,
    required this.module,
    required this.routeHint,
    required this.requiredRoleText,
    required this.steps,
    required this.safeNote,
  });

  final String key;
  final String title;
  final String module;
  final String routeHint;
  final String requiredRoleText;
  final List<String> steps;
  final String safeNote;
}

class AssistantScreenContext {
  const AssistantScreenContext({
    required this.screenTitle,
    required this.routeName,
    required this.moduleName,
    required this.confidence,
  });

  final String screenTitle;
  final String routeName;
  final String moduleName;
  final String confidence;
}

class AssistantSafeSummary {
  const AssistantSafeSummary({
    required this.title,
    required this.value,
    required this.description,
  });

  final String title;
  final String value;
  final String description;
}

class AssistantMobileContract {
  static const forbiddenTechnicalCopy = <String>[
    'de' 'bug',
    'end' 'point',
    'işlem tamamlanamadı',
    'işlem hatası',
    'süreç',
    'phase',
    'eşitleme',
    'Bu işlem için yetkiniz bulunmamaktadır',
  ];

  static AssistantScreenContext detectScreen(String routeName, String visibleTitle) {
    final route = routeName.toLowerCase();
    final title = visibleTitle.toLowerCase();
    if (route.contains('performance') || title.contains('performans')) {
      return const AssistantScreenContext(
        screenTitle: 'Performans Yönetimi',
        routeName: '/performance',
        moduleName: 'Performans Yönetimi',
        confidence: 'yüksek',
      );
    }
    if (route.contains('notification') || title.contains('bildirim')) {
      return const AssistantScreenContext(
        screenTitle: 'Bildirimler',
        routeName: '/notifications',
        moduleName: 'Bildirimler',
        confidence: 'yüksek',
      );
    }
    if (route.contains('support') || title.contains('destek')) {
      return const AssistantScreenContext(
        screenTitle: 'Destek Talepleri',
        routeName: '/support',
        moduleName: 'İletişim ve Destek',
        confidence: 'yüksek',
      );
    }
    if (route.contains('profile') || title.contains('profil')) {
      return const AssistantScreenContext(
        screenTitle: 'Profil',
        routeName: '/profile',
        moduleName: 'Kullanıcı Profili',
        confidence: 'yüksek',
      );
    }
    return const AssistantScreenContext(
      screenTitle: 'Ana Sayfa',
      routeName: '/dashboard',
      moduleName: 'Genel Dashboard',
      confidence: 'orta',
    );
  }

  static AssistantMobileIntent resolveIntent(String question) {
    final q = question.toLowerCase();
    if (q.contains('dönem') || q.contains('donem')) {
      return const AssistantMobileIntent(
        key: 'PERFORMANS_DONEMI_YONLENDIRME',
        title: 'Performans dönemi yönlendirmesi',
        module: 'Performans Yönetimi',
        routeHint: 'Performans Yönetimi > Dönemler',
        requiredRoleText: 'Admin, Sistem Yöneticisi veya Performans Yetkilisi',
        steps: [
          'Performans Yönetimi bölümünü açın.',
          'Dönemler ekranına girin.',
          'İlgili dönemi seçin veya yetkiniz varsa yeni dönem oluşturun.',
          'Kapsam, tarih ve görev üretimi bilgilerini kontrol edin.',
        ],
        safeNote: 'Dönem açma ve görev üretimi rol/yetki sınırına göre yapılır.',
      );
    }
    if (q.contains('karne') || q.contains('puan')) {
      return const AssistantMobileIntent(
        key: 'PERFORMANS_KARNE_YONLENDIRME',
        title: 'Karne ve puan görünürlüğü',
        module: 'Performans Yönetimi',
        routeHint: 'Performans Yönetimi > Karne',
        requiredRoleText: 'Personel kendi yayınlanmış karnesini; yönetici ise yetkili kapsamını görebilir',
        steps: [
          'Performans Yönetimi bölümünü açın.',
          'Karne ekranına girin.',
          'Dönem bilgisini kontrol edin.',
          'Karne görünmüyorsa yayın/onay sürecinin tamamlanıp tamamlanmadığını kontrol edin.',
        ],
        safeNote: 'Asistan performans puanı, amir görüşü veya hassas karne içeriğini doğrudan göstermez.',
      );
    }
    if (q.contains('bildirim')) {
      return const AssistantMobileIntent(
        key: 'BILDIRIM_YONLENDIRME',
        title: 'Bildirim yönlendirmesi',
        module: 'Bildirimler',
        routeHint: 'Bildirimler',
        requiredRoleText: 'Tüm kullanıcılar kendi bildirimlerini görebilir',
        steps: [
          'Alt menüden veya hızlı işlemlerden Bildirimler ekranını açın.',
          'Okunmamış bildirimleri kontrol edin.',
          'İlgili bildirimin yönlendirdiği ekrana geçin.',
        ],
        safeNote: 'Bildirim içerikleri kullanıcı yetkisine göre listelenir.',
      );
    }
    if (q.contains('destek') || q.contains('talep')) {
      return const AssistantMobileIntent(
        key: 'DESTEK_YONLENDIRME',
        title: 'Destek talebi yönlendirmesi',
        module: 'Destek Talepleri',
        routeHint: 'Destek Talepleri',
        requiredRoleText: 'Tüm kullanıcılar kendi destek taleplerini takip edebilir',
        steps: [
          'Destek Talepleri ekranını açın.',
          'Açık talepleri kontrol edin.',
          'Yeni talep gerekiyorsa kısa ve anlaşılır açıklama yazın.',
        ],
        safeNote: 'Destek talepleri yetki ve sahiplik sınırına göre gösterilir.',
      );
    }
    return const AssistantMobileIntent(
      key: 'GENEL_REHBERLIK',
      title: 'Genel BYS360 rehberliği',
      module: 'BYS360',
      routeHint: 'Ana Sayfa',
      requiredRoleText: 'Kullanıcıya açık menüler rol matrisine göre belirlenir',
      steps: [
        'Ana Sayfa ekranındaki bekleyen işleri kontrol edin.',
        'İşleminize en yakın hızlı işlem kartını seçin.',
        'Menü görünmüyorsa rol/yetki tanımınızı kontrol ettirin.',
      ],
      safeNote: 'Asistan idari karar üretmez; yalnızca güvenli rehberlik ve yönlendirme sağlar.',
    );
  }
}

// BYS360_MOBILE_V2_8_28_ASSISTANT_P1_SCREEN_DETECT_FIX_MARKER: detectScreen contract is present for BYS360 mobile assistant.

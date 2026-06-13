class SimpleItem {
  SimpleItem({required this.id, required this.title, this.subtitle, this.status});

  final String id;
  final String title;
  final String? subtitle;
  final String? status;

  factory SimpleItem.fromJson(Map<String, dynamic> json) {
    return SimpleItem(
      id: json['id']?.toString() ?? '',
      title: (json['title'] ?? json['full_name'] ?? json['subject'] ?? 'Kayıt').toString(),
      subtitle: (json['subtitle'] ?? json['unit'] ?? json['body'] ?? json['message'])?.toString(),
      status: (json['status'] ?? json['title_text'])?.toString(),
    );
  }
}

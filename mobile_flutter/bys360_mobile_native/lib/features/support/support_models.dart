import '../../core/utils/bys360_status_labels.dart';

class SupportTicketDetail {
  const SupportTicketDetail({
    required this.ticket,
    required this.messages,
    required this.statusHistory,
    required this.attachments,
    required this.canReply,
    required this.canManage,
  });

  final SupportTicketInfo ticket;
  final List<SupportTicketMessageItem> messages;
  final List<SupportStatusHistoryItem> statusHistory;
  final List<SupportAttachmentItem> attachments;
  final bool canReply;
  final bool canManage;

  factory SupportTicketDetail.fromJson(Map<String, dynamic> json) {
    final ticketMap = json['ticket'] is Map ? Map<String, dynamic>.from(json['ticket'] as Map) : <String, dynamic>{};
    final messageList = json['messages'] is List ? json['messages'] as List : const [];
    final historyList = json['status_history'] is List ? json['status_history'] as List : const [];
    final attachmentList = json['attachments'] is List ? json['attachments'] as List : const [];

    return SupportTicketDetail(
      ticket: SupportTicketInfo.fromJson(ticketMap),
      messages: messageList.map((item) => SupportTicketMessageItem.fromJson(Map<String, dynamic>.from(item as Map))).toList(),
      statusHistory: historyList.map((item) => SupportStatusHistoryItem.fromJson(Map<String, dynamic>.from(item as Map))).toList(),
      attachments: attachmentList.map((item) => SupportAttachmentItem.fromJson(Map<String, dynamic>.from(item as Map))).toList(),
      canReply: json['can_reply'] == true,
      canManage: json['can_manage'] == true,
    );
  }
}

class SupportTicketInfo {
  const SupportTicketInfo({
    required this.id,
    required this.ticketNo,
    required this.title,
    required this.description,
    required this.status,
    required this.statusLabel,
    required this.priority,
    required this.priorityLabel,
    required this.moduleName,
    required this.ticketType,
    required this.requesterName,
    required this.unitName,
    required this.sicilNo,
    required this.assignedTo,
    required this.createdAt,
    required this.updatedAt,
    required this.elapsedLabel,
    required this.subStatusText,
    required this.resolutionText,
  });

  final String id;
  final String ticketNo;
  final String title;
  final String description;
  final String status;
  final String statusLabel;
  final String priority;
  final String priorityLabel;
  final String moduleName;
  final String ticketType;
  final String requesterName;
  final String unitName;
  final String sicilNo;
  final String assignedTo;
  final String createdAt;
  final String updatedAt;
  final String elapsedLabel;
  final String subStatusText;
  final String resolutionText;

  bool get isClosed => {'closed', 'resolved', 'rejected', 'kapalı', 'kapali', 'çözüldü', 'cozuldu'}.contains(status.toLowerCase());

  factory SupportTicketInfo.fromJson(Map<String, dynamic> json) {
    return SupportTicketInfo(
      id: json['id']?.toString() ?? '',
      ticketNo: json['ticket_no']?.toString() ?? '-',
      title: json['title']?.toString() ?? 'Destek talebi',
      description: json['description']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      statusLabel: json['status_label']?.toString() ?? bys360GenericStatusLabel(json['status']?.toString(), fallback: '-'),
      priority: json['priority']?.toString() ?? '',
      priorityLabel: json['priority_label']?.toString() ?? bys360GenericStatusLabel(json['priority']?.toString(), fallback: '-'),
      moduleName: json['module_name']?.toString() ?? 'Genel',
      ticketType: json['ticket_type']?.toString() ?? '-',
      requesterName: json['requester_name']?.toString() ?? '-',
      unitName: json['unit_name']?.toString() ?? '-',
      sicilNo: json['sicil_no']?.toString() ?? '-',
      assignedTo: json['assigned_to']?.toString() ?? 'Atanmadı',
      createdAt: json['created_at']?.toString() ?? '-',
      updatedAt: json['updated_at']?.toString() ?? '-',
      elapsedLabel: json['elapsed_label']?.toString() ?? '-',
      subStatusText: json['sub_status_text']?.toString() ?? '-',
      resolutionText: json['resolution_text']?.toString() ?? '-',
    );
  }
}

class SupportTicketMessageItem {
  const SupportTicketMessageItem({required this.id, required this.author, required this.message, required this.createdAt, required this.isInternal});

  final String id;
  final String author;
  final String message;
  final String createdAt;
  final bool isInternal;

  factory SupportTicketMessageItem.fromJson(Map<String, dynamic> json) {
    return SupportTicketMessageItem(
      id: json['id']?.toString() ?? '',
      author: json['author']?.toString() ?? 'Kullanıcı',
      message: json['message']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '-',
      isInternal: json['is_internal'] == true,
    );
  }
}

class SupportStatusHistoryItem {
  const SupportStatusHistoryItem({required this.id, required this.changedBy, required this.oldStatus, required this.newStatus, required this.note, required this.createdAt});

  final String id;
  final String changedBy;
  final String oldStatus;
  final String newStatus;
  final String note;
  final String createdAt;

  factory SupportStatusHistoryItem.fromJson(Map<String, dynamic> json) {
    return SupportStatusHistoryItem(
      id: json['id']?.toString() ?? '',
      changedBy: json['changed_by']?.toString() ?? 'Sistem',
      oldStatus: bys360GenericStatusLabel(json['old_status']?.toString(), fallback: 'İlk kayıt'),
      newStatus: bys360GenericStatusLabel(json['new_status']?.toString(), fallback: '-'),
      note: json['note']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '-',
    );
  }
}

class SupportAttachmentItem {
  const SupportAttachmentItem({required this.id, required this.filename, required this.sizeLabel, required this.mimeType});

  final String id;
  final String filename;
  final String sizeLabel;
  final String mimeType;

  factory SupportAttachmentItem.fromJson(Map<String, dynamic> json) {
    return SupportAttachmentItem(
      id: json['id']?.toString() ?? '',
      filename: json['filename']?.toString() ?? 'Dosya',
      sizeLabel: json['size_label']?.toString() ?? '-',
      mimeType: json['mime_type']?.toString() ?? '-',
    );
  }
}

// support_reply
// support_contract
// BYS360_MOBILE_V2_8_32_SUPPORT_SURVEY_P1_REPLY_FIX

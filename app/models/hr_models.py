"""İzin, devamsızlık, vekâlet ve profesyonel Personel operasyon modelleri."""

from .base import TimestampMixin, db


class LeaveBalance(TimestampMixin, db.Model):
    __tablename__ = "leave_balances"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = db.Column(db.String(50), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=True, index=True)
    total_days = db.Column(db.Float, default=0.0, nullable=False)
    carried_over_days = db.Column(db.Float, default=0.0, nullable=False)
    used_days = db.Column(db.Float, default=0.0, nullable=False)
    manual_override = db.Column(db.Boolean, default=False, nullable=False)
    note = db.Column(db.Text, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="leave_balances")

    __table_args__ = (
        db.UniqueConstraint("user_id", "leave_type", "year", name="uq_leave_balance_user_type_year"),
    )

    @property
    def remaining_days(self) -> float:
        return round(float(self.total_days or 0) + float(self.carried_over_days or 0) - float(self.used_days or 0), 2)


class PersonnelLeave(TimestampMixin, db.Model):
    __tablename__ = "personnel_leaves"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    period_id = db.Column(db.Integer, db.ForeignKey("performance_periods.id", ondelete="SET NULL"), nullable=True, index=True)
    leave_type = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(db.String(30), default="onaylandi", nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    approved_day_count = db.Column(db.Float, nullable=True)
    start_half_day = db.Column(db.Boolean, default=False, nullable=False)
    end_half_day = db.Column(db.Boolean, default=False, nullable=False)
    blocks_performance_evaluation = db.Column(db.Boolean, default=True, nullable=False)
    performance_mode = db.Column(db.String(20), default="partial", nullable=False, index=True)
    blocks_manager_duties = db.Column(db.Boolean, default=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="leave_requests")
    approved_by = db.relationship("User", foreign_keys=[approved_by_id], back_populates="approved_leave_requests")
    period = db.relationship("PerformancePeriod", back_populates="leave_requests")


class AttendanceException(TimestampMixin, db.Model):
    __tablename__ = "attendance_exceptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    period_id = db.Column(db.Integer, db.ForeignKey("performance_periods.id", ondelete="SET NULL"), nullable=True, index=True)
    record_date = db.Column(db.Date, nullable=False, index=True)
    exception_type = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(db.String(30), default="onaylandi", nullable=False, index=True)
    day_fraction = db.Column(db.Float, default=1.0, nullable=False)
    blocks_performance_evaluation = db.Column(db.Boolean, default=True, nullable=False)
    performance_mode = db.Column(db.String(20), default="partial", nullable=False, index=True)
    blocks_manager_duties = db.Column(db.Boolean, default=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="attendance_exceptions")
    approved_by = db.relationship("User", foreign_keys=[approved_by_id], back_populates="approved_attendance_exceptions")
    period = db.relationship("PerformancePeriod", back_populates="attendance_exceptions")


class DelegationAssignment(TimestampMixin, db.Model):
    __tablename__ = "delegation_assignments"

    id = db.Column(db.Integer, primary_key=True)
    delegator_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    delegate_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_leave_id = db.Column(db.Integer, db.ForeignKey("personnel_leaves.id", ondelete="SET NULL"), nullable=True, index=True)
    source_attendance_id = db.Column(db.Integer, db.ForeignKey("attendance_exceptions.id", ondelete="SET NULL"), nullable=True, index=True)
    status = db.Column(db.String(30), default="aktif", nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    scope_type = db.Column(db.String(30), default="performance", nullable=False)
    applies_level_1 = db.Column(db.Boolean, default=True, nullable=False)
    applies_level_2 = db.Column(db.Boolean, default=True, nullable=False)
    applies_level_3 = db.Column(db.Boolean, default=True, nullable=False)
    note = db.Column(db.Text, nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    delegator = db.relationship("User", foreign_keys=[delegator_user_id], back_populates="delegations_given")
    delegate = db.relationship("User", foreign_keys=[delegate_user_id], back_populates="delegations_received")
    approved_by = db.relationship("User", foreign_keys=[approved_by_id], back_populates="approved_delegations")
    source_leave = db.relationship("PersonnelLeave", foreign_keys=[source_leave_id])
    source_attendance = db.relationship("AttendanceException", foreign_keys=[source_attendance_id])


class PersonnelDocumentCategory(TimestampMixin, db.Model):
    __tablename__ = "personnel_document_categories"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True, index=True)
    label = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_required = db.Column(db.Boolean, default=False, nullable=False, index=True)
    validity_days = db.Column(db.Integer, nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)


class PersonnelDocument(TimestampMixin, db.Model):
    __tablename__ = "personnel_documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, default="ozluk", index=True)
    title = db.Column(db.String(255), nullable=False)
    document_no = db.Column(db.String(120), nullable=True, index=True)
    status = db.Column(db.String(30), nullable=False, default="aktif", index=True)
    issue_date = db.Column(db.Date, nullable=True, index=True)
    expiry_date = db.Column(db.Date, nullable=True, index=True)
    original_filename = db.Column(db.String(255), nullable=True)
    stored_filename = db.Column(db.String(255), nullable=True)
    storage_path = db.Column(db.String(500), nullable=True)
    mime_type = db.Column(db.String(150), nullable=True)
    file_size = db.Column(db.BigInteger, default=0, nullable=False)
    is_confidential = db.Column(db.Boolean, default=False, nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    description = db.Column(db.Text, nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_documents", lazy="noload", cascade="save-update, merge",
            passive_deletes=True),
    
        passive_deletes=True)
    uploaded_by = db.relationship(
        "User",
        foreign_keys=[uploaded_by_id],
        backref=db.backref("uploaded_personnel_documents", lazy="noload",
            passive_deletes=True,
            cascade="save-update, merge"),
    
        passive_deletes=True,
        cascade="save-update, merge")


class PersonnelDocumentUploadBatch(TimestampMixin, db.Model):
    __tablename__ = "personnel_document_upload_batches"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    category_code = db.Column(db.String(50), nullable=True, index=True)
    status = db.Column(db.String(30), nullable=False, default="tamamlandi", index=True)
    source_name = db.Column(db.String(255), nullable=True)
    total_file_count = db.Column(db.Integer, nullable=False, default=0)
    success_count = db.Column(db.Integer, nullable=False, default=0)
    note = db.Column(db.Text, nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_document_upload_batches", lazy="noload", cascade="save-update, merge",
            passive_deletes=True),
    )
    uploaded_by = db.relationship(
        "User",
        foreign_keys=[uploaded_by_id],
        backref=db.backref("uploaded_personnel_document_batches", lazy="noload",
            passive_deletes=True,
            cascade="save-update, merge"),
    )


class PersonnelProcessNote(TimestampMixin, db.Model):
    __tablename__ = "personnel_process_notes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    note_type = db.Column(db.String(50), nullable=False, default="ozluk", index=True)
    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    subject = db.Column(db.String(255), nullable=False)
    note = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="open", index=True)
    due_date = db.Column(db.Date, nullable=True, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    is_private = db.Column(db.Boolean, default=True, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_process_notes", lazy="noload", cascade="save-update, merge",
            passive_deletes=True),
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        backref=db.backref("created_personnel_process_notes", lazy="noload",
            passive_deletes=True,
            cascade="save-update, merge"),
    )


class PersonnelStatusHistory(TimestampMixin, db.Model):
    __tablename__ = "personnel_status_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, default="durum", index=True)
    event_date = db.Column(db.Date, nullable=False, index=True)
    effective_start_date = db.Column(db.Date, nullable=True, index=True)
    effective_end_date = db.Column(db.Date, nullable=True, index=True)
    organization_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True)
    previous_value = db.Column(db.String(255), nullable=True)
    new_value = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_status_history", lazy="dynamic", cascade="all, delete-orphan"),
    )
    organization_unit = db.relationship(
        "OrganizationUnit",
        foreign_keys=[organization_unit_id],
        backref=db.backref("personnel_status_history", lazy="dynamic"),
    )
    recorded_by = db.relationship(
        "User",
        foreign_keys=[recorded_by_id],
        backref=db.backref("recorded_personnel_status_history", lazy="dynamic"),
    )

class PersonnelSelfServiceRequestTemplate(TimestampMixin, db.Model):
    __tablename__ = "personnel_self_service_request_templates"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True, index=True)
    request_type = db.Column(db.String(50), nullable=False, default="bilgi_guncelleme", index=True)
    title = db.Column(db.String(255), nullable=False)
    description_hint = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    sla_target_days = db.Column(db.Integer, nullable=True)
    requires_attachment = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)


class PersonnelSelfServiceRequest(TimestampMixin, db.Model):
    __tablename__ = "personnel_self_service_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    current_handler_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    last_action_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey("personnel_self_service_request_templates.id", ondelete="SET NULL"), nullable=True, index=True)

    request_type = db.Column(db.String(50), nullable=False, default="bilgi_guncelleme", index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)

    requested_effective_date = db.Column(db.Date, nullable=True, index=True)
    desired_completion_date = db.Column(db.Date, nullable=True, index=True)
    submitted_at = db.Column(db.DateTime, nullable=True, index=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    first_response_at = db.Column(db.DateTime, nullable=True)
    due_at = db.Column(db.DateTime, nullable=True, index=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    sla_target_days = db.Column(db.Integer, nullable=True)
    requires_attachment = db.Column(db.Boolean, default=False, nullable=False)

    decision_note = db.Column(db.Text, nullable=True)
    hr_visible = db.Column(db.Boolean, default=True, nullable=False, index=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_self_service_requests", lazy="dynamic", cascade="all, delete-orphan"),
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        backref=db.backref("created_personnel_self_service_requests", lazy="dynamic"),
    )
    current_handler = db.relationship(
        "User",
        foreign_keys=[current_handler_id],
        backref=db.backref("assigned_personnel_self_service_requests", lazy="dynamic"),
    )
    last_action_by = db.relationship(
        "User",
        foreign_keys=[last_action_by_id],
        backref=db.backref("acted_personnel_self_service_requests", lazy="dynamic"),
    )
    template = db.relationship(
        "PersonnelSelfServiceRequestTemplate",
        foreign_keys=[template_id],
        backref=db.backref("requests", lazy="dynamic"),
    )


class PersonnelSelfServiceRequestAttachment(TimestampMixin, db.Model):
    __tablename__ = "personnel_self_service_request_attachments"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("personnel_self_service_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=True)
    storage_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(150), nullable=True)
    file_size = db.Column(db.BigInteger, default=0, nullable=False)
    note = db.Column(db.String(255), nullable=True)

    request = db.relationship(
        "PersonnelSelfServiceRequest",
        foreign_keys=[request_id],
        backref=db.backref("attachments", lazy="dynamic", cascade="all, delete-orphan"),
    )
    uploaded_by = db.relationship(
        "User",
        foreign_keys=[uploaded_by_id],
        backref=db.backref("personnel_self_service_request_attachments", lazy="dynamic"),
    )


class PersonnelSelfServiceRequestLog(TimestampMixin, db.Model):
    __tablename__ = "personnel_self_service_request_logs"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("personnel_self_service_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False, default="created", index=True)
    from_status = db.Column(db.String(30), nullable=True, index=True)
    to_status = db.Column(db.String(30), nullable=True, index=True)
    note = db.Column(db.Text, nullable=True)

    request = db.relationship(
        "PersonnelSelfServiceRequest",
        foreign_keys=[request_id],
        backref=db.backref("logs", lazy="dynamic", cascade="all, delete-orphan"),
    )
    actor = db.relationship(
        "User",
        foreign_keys=[actor_user_id],
        backref=db.backref("personnel_self_service_request_logs", lazy="dynamic"),
    )


class PersonnelSelfServiceRequestTask(TimestampMixin, db.Model):
    __tablename__ = "personnel_self_service_request_tasks"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("personnel_self_service_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    task_type = db.Column(db.String(50), nullable=False, default="review", index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="open", index=True)
    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    due_at = db.Column(db.DateTime, nullable=True, index=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True, index=True)
    is_primary = db.Column(db.Boolean, default=True, nullable=False, index=True)

    note = db.Column(db.Text, nullable=True)
    completion_note = db.Column(db.Text, nullable=True)

    request = db.relationship(
        "PersonnelSelfServiceRequest",
        foreign_keys=[request_id],
        backref=db.backref("tasks", lazy="dynamic", cascade="all, delete-orphan"),
    )
    assigned_to = db.relationship(
        "User",
        foreign_keys=[assigned_to_id],
        backref=db.backref("assigned_personnel_request_tasks", lazy="dynamic"),
    )
    assigned_by = db.relationship(
        "User",
        foreign_keys=[assigned_by_id],
        backref=db.backref("delegated_personnel_request_tasks", lazy="dynamic"),
    )

# Compatibility guard.
class PersonnelSelfServiceRequestSlaPolicy(TimestampMixin, db.Model):
    __tablename__ = "personnel_self_service_request_sla_policies"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True, index=True)
    request_type = db.Column(db.String(50), nullable=False, index=True)
    priority = db.Column(db.String(20), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    target_days = db.Column(db.Integer, nullable=False, default=3)
    first_response_hours = db.Column(db.Integer, nullable=True)
    escalation_hours = db.Column(db.Integer, nullable=True)
    owner_role = db.Column(db.String(50), nullable=True, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    note = db.Column(db.Text, nullable=True)


class PersonnelSelfServiceRequestEscalation(TimestampMixin, db.Model):
    __tablename__ = "personnel_self_service_request_escalations"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("personnel_self_service_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey("personnel_self_service_request_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    escalated_from_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    escalated_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    escalated_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    level = db.Column(db.Integer, nullable=False, default=1, index=True)
    status = db.Column(db.String(30), nullable=False, default="open", index=True)
    reason = db.Column(db.String(255), nullable=False)
    note = db.Column(db.Text, nullable=True)
    escalated_at = db.Column(db.DateTime, nullable=True, index=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    request = db.relationship(
        "PersonnelSelfServiceRequest",
        foreign_keys=[request_id],
        backref=db.backref("escalations", lazy="dynamic", cascade="all, delete-orphan"),
    )
    task = db.relationship(
        "PersonnelSelfServiceRequestTask",
        foreign_keys=[task_id],
        backref=db.backref("escalations", lazy="dynamic"),
    )
    escalated_from_user = db.relationship(
        "User",
        foreign_keys=[escalated_from_user_id],
        backref=db.backref("personnel_request_escalations_from", lazy="dynamic"),
    )
    escalated_to_user = db.relationship(
        "User",
        foreign_keys=[escalated_to_user_id],
        backref=db.backref("personnel_request_escalations_to", lazy="dynamic"),
    )
    escalated_by = db.relationship(
        "User",
        foreign_keys=[escalated_by_id],
        backref=db.backref("personnel_request_escalations_by", lazy="dynamic"),
    )


class PersonnelPositionHistory(TimestampMixin, db.Model):
    __tablename__ = "personnel_position_histories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True)
    manager_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    position_title = db.Column(db.String(150), nullable=False, index=True)
    position_grade = db.Column(db.String(50), nullable=True)
    assignment_type = db.Column(db.String(50), nullable=False, default="atama", index=True)
    appointment_kind = db.Column(db.String(50), nullable=True, index=True)
    decision_no = db.Column(db.String(120), nullable=True, index=True)

    start_date = db.Column(db.Date, nullable=True, index=True)
    end_date = db.Column(db.Date, nullable=True, index=True)
    reason = db.Column(db.Text, nullable=True)
    is_current = db.Column(db.Boolean, default=False, nullable=False, index=True)

    unit_name_snapshot = db.Column(db.String(255), nullable=True)
    parent_unit_name_snapshot = db.Column(db.String(255), nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_position_histories", lazy="dynamic", cascade="all, delete-orphan"),
    )
    organization_unit = db.relationship(
        "OrganizationUnit",
        foreign_keys=[organization_unit_id],
        backref=db.backref("personnel_position_histories", lazy="dynamic"),
    )
    manager_user = db.relationship(
        "User",
        foreign_keys=[manager_user_id],
        backref=db.backref("managed_personnel_position_histories", lazy="dynamic"),
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        backref=db.backref("created_personnel_position_histories", lazy="dynamic"),
    )


class PersonnelAssetAssignment(TimestampMixin, db.Model):
    __tablename__ = "personnel_asset_assignments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_category = db.Column(db.String(50), nullable=False, default="demirbas", index=True)
    asset_name = db.Column(db.String(255), nullable=False)
    asset_code = db.Column(db.String(120), nullable=True, index=True)
    serial_no = db.Column(db.String(120), nullable=True, index=True)
    status = db.Column(db.String(30), nullable=False, default="assigned", index=True)
    assigned_date = db.Column(db.Date, nullable=False, index=True)
    due_return_date = db.Column(db.Date, nullable=True, index=True)
    returned_date = db.Column(db.Date, nullable=True, index=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    received_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note = db.Column(db.Text, nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_asset_assignments", lazy="dynamic", cascade="all, delete-orphan"),
    )
    assigned_by = db.relationship(
        "User",
        foreign_keys=[assigned_by_id],
        backref=db.backref("assigned_personnel_assets", lazy="dynamic"),
    )
    received_by = db.relationship(
        "User",
        foreign_keys=[received_by_id],
        backref=db.backref("received_personnel_assets", lazy="dynamic"),
    )


class PersonnelChecklistTemplateItem(TimestampMixin, db.Model):
    __tablename__ = "personnel_checklist_template_items"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True, index=True)
    label = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="ozluk", index=True)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_required = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)


class PersonnelChecklistReview(TimestampMixin, db.Model):
    __tablename__ = "personnel_checklist_reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_item_id = db.Column(db.Integer, db.ForeignKey("personnel_checklist_template_items.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    checked_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    checked_at = db.Column(db.DateTime, nullable=True, index=True)
    expiry_date = db.Column(db.Date, nullable=True, index=True)
    note = db.Column(db.Text, nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_checklist_reviews", lazy="dynamic", cascade="all, delete-orphan"),
    )
    template_item = db.relationship(
        "PersonnelChecklistTemplateItem",
        foreign_keys=[template_item_id],
        backref=db.backref("reviews", lazy="dynamic", cascade="all, delete-orphan"),
    )
    checked_by = db.relationship(
        "User",
        foreign_keys=[checked_by_id],
        backref=db.backref("checked_personnel_checklists", lazy="dynamic"),
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "template_item_id", name="uq_personnel_checklist_user_template"),
    )


class PersonnelDocumentReminderLog(TimestampMixin, db.Model):
    __tablename__ = "personnel_document_reminder_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey("personnel_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_type = db.Column(db.String(30), nullable=False, default="manual", index=True)
    channel = db.Column(db.String(30), nullable=False, default="in_app", index=True)
    status = db.Column(db.String(30), nullable=False, default="queued", index=True)
    due_date = db.Column(db.Date, nullable=True, index=True)
    reminder_text = db.Column(db.Text, nullable=True)
    triggered_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    triggered_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_document_reminder_logs", lazy="noload", cascade="save-update, merge",
            passive_deletes=True),
    )
    document = db.relationship(
        "PersonnelDocument",
        foreign_keys=[document_id],
        backref=db.backref("reminder_logs", lazy="noload", cascade="save-update, merge",
            passive_deletes=True),
    
        passive_deletes=True)
    triggered_by = db.relationship(
        "User",
        foreign_keys=[triggered_by_id],
        backref=db.backref("triggered_personnel_document_reminders", lazy="noload",
            passive_deletes=True,
            cascade="save-update, merge"),
    )


class PersonnelAssetTransferLog(TimestampMixin, db.Model):
    __tablename__ = "personnel_asset_transfer_logs"

    id = db.Column(db.Integer, primary_key=True)
    asset_assignment_id = db.Column(db.Integer, db.ForeignKey("personnel_asset_assignments.id", ondelete="SET NULL"), nullable=True, index=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    transferred_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    transfer_date = db.Column(db.Date, nullable=False, index=True)
    transfer_type = db.Column(db.String(30), nullable=False, default="devir", index=True)
    handover_status = db.Column(db.String(30), nullable=False, default="completed", index=True)
    handover_document_no = db.Column(db.String(120), nullable=True, index=True)

    asset_name_snapshot = db.Column(db.String(255), nullable=False)
    asset_code_snapshot = db.Column(db.String(120), nullable=True, index=True)
    serial_no_snapshot = db.Column(db.String(120), nullable=True, index=True)
    note = db.Column(db.Text, nullable=True)

    asset_assignment = db.relationship(
        "PersonnelAssetAssignment",
        foreign_keys=[asset_assignment_id],
        backref=db.backref("transfer_logs", lazy="dynamic"),
    )
    from_user = db.relationship(
        "User",
        foreign_keys=[from_user_id],
        backref=db.backref("outgoing_personnel_asset_transfers", lazy="dynamic"),
    )
    to_user = db.relationship(
        "User",
        foreign_keys=[to_user_id],
        backref=db.backref("incoming_personnel_asset_transfers", lazy="dynamic"),
    )
    transferred_by = db.relationship(
        "User",
        foreign_keys=[transferred_by_id],
        backref=db.backref("processed_personnel_asset_transfers", lazy="dynamic"),
    )


class PersonnelLifecycleCase(TimestampMixin, db.Model):
    __tablename__ = "personnel_lifecycle_cases"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    coordinator_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    lifecycle_type = db.Column(db.String(50), nullable=False, default="onboarding", index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    priority = db.Column(db.String(20), nullable=False, default="normal", index=True)
    start_date = db.Column(db.Date, nullable=True, index=True)
    target_date = db.Column(db.Date, nullable=True, index=True)
    completed_at = db.Column(db.DateTime, nullable=True, index=True)
    decision_no = db.Column(db.String(120), nullable=True, index=True)
    summary = db.Column(db.Text, nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_lifecycle_cases", lazy="dynamic", cascade="all, delete-orphan"),
    )
    organization_unit = db.relationship(
        "OrganizationUnit",
        foreign_keys=[organization_unit_id],
        backref=db.backref("personnel_lifecycle_cases", lazy="dynamic"),
    )
    owner_user = db.relationship(
        "User",
        foreign_keys=[owner_user_id],
        backref=db.backref("owned_personnel_lifecycle_cases", lazy="dynamic"),
    )
    coordinator_user = db.relationship(
        "User",
        foreign_keys=[coordinator_user_id],
        backref=db.backref("coordinated_personnel_lifecycle_cases", lazy="dynamic"),
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        backref=db.backref("created_personnel_lifecycle_cases", lazy="dynamic"),
    )


class PersonnelLifecycleTask(TimestampMixin, db.Model):
    __tablename__ = "personnel_lifecycle_tasks"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("personnel_lifecycle_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    category = db.Column(db.String(50), nullable=False, default="genel", index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    due_date = db.Column(db.Date, nullable=True, index=True)
    completed_at = db.Column(db.DateTime, nullable=True, index=True)
    is_required = db.Column(db.Boolean, default=True, nullable=False, index=True)
    note = db.Column(db.Text, nullable=True)

    case = db.relationship(
        "PersonnelLifecycleCase",
        foreign_keys=[case_id],
        backref=db.backref("tasks", lazy="dynamic", cascade="all, delete-orphan"),
    )
    assigned_to = db.relationship(
        "User",
        foreign_keys=[assigned_to_id],
        backref=db.backref("assigned_personnel_lifecycle_tasks", lazy="dynamic"),
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        backref=db.backref("created_personnel_lifecycle_tasks", lazy="dynamic"),
    )


class PersonnelExitInterview(TimestampMixin, db.Model):
    __tablename__ = "personnel_exit_interviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lifecycle_case_id = db.Column(db.Integer, db.ForeignKey("personnel_lifecycle_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    interviewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    interview_date = db.Column(db.Date, nullable=False, index=True)
    separation_reason = db.Column(db.String(50), nullable=True, index=True)
    satisfaction_score = db.Column(db.Integer, nullable=True)
    would_rehire = db.Column(db.Boolean, default=True, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    risk_flags = db.Column(db.Text, nullable=True)
    action_note = db.Column(db.Text, nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_exit_interviews", lazy="dynamic", cascade="all, delete-orphan"),
    )
    lifecycle_case = db.relationship(
        "PersonnelLifecycleCase",
        foreign_keys=[lifecycle_case_id],
        backref=db.backref("exit_interviews", lazy="dynamic"),
    )
    interviewed_by = db.relationship(
        "User",
        foreign_keys=[interviewed_by_id],
        backref=db.backref("conducted_personnel_exit_interviews", lazy="dynamic"),
    )

class PersonnelHandoverRecord(TimestampMixin, db.Model):
    __tablename__ = "personnel_handover_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lifecycle_case_id = db.Column(db.Integer, db.ForeignKey("personnel_lifecycle_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_unit_id = db.Column(db.Integer, db.ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    operation_type = db.Column(db.String(30), nullable=False, default="offboarding", index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    planned_date = db.Column(db.Date, nullable=True, index=True)
    due_date = db.Column(db.Date, nullable=True, index=True)
    completed_at = db.Column(db.DateTime, nullable=True, index=True)
    handover_no = db.Column(db.String(120), nullable=True, index=True)
    note = db.Column(db.Text, nullable=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_handover_records", lazy="dynamic", cascade="all, delete-orphan"),
    )
    lifecycle_case = db.relationship(
        "PersonnelLifecycleCase",
        foreign_keys=[lifecycle_case_id],
        backref=db.backref("handover_records", lazy="dynamic"),
    )
    organization_unit = db.relationship(
        "OrganizationUnit",
        foreign_keys=[organization_unit_id],
        backref=db.backref("personnel_handover_records", lazy="dynamic"),
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        backref=db.backref("created_personnel_handover_records", lazy="dynamic"),
    )
    approved_by = db.relationship(
        "User",
        foreign_keys=[approved_by_id],
        backref=db.backref("approved_personnel_handover_records", lazy="dynamic"),
    )


class PersonnelHandoverItem(TimestampMixin, db.Model):
    __tablename__ = "personnel_handover_items"

    id = db.Column(db.Integer, primary_key=True)
    handover_id = db.Column(db.Integer, db.ForeignKey("personnel_handover_records.id", ondelete="CASCADE"), nullable=False, index=True)
    responsible_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    category = db.Column(db.String(50), nullable=False, default="genel", index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    due_date = db.Column(db.Date, nullable=True, index=True)
    completed_at = db.Column(db.DateTime, nullable=True, index=True)
    is_required = db.Column(db.Boolean, default=True, nullable=False, index=True)
    evidence_note = db.Column(db.Text, nullable=True)
    note = db.Column(db.Text, nullable=True)

    handover = db.relationship(
        "PersonnelHandoverRecord",
        foreign_keys=[handover_id],
        backref=db.backref("items", lazy="dynamic", cascade="all, delete-orphan"),
    )
    responsible_user = db.relationship(
        "User",
        foreign_keys=[responsible_user_id],
        backref=db.backref("assigned_personnel_handover_items", lazy="dynamic"),
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        backref=db.backref("created_personnel_handover_items", lazy="dynamic"),
    )

class PersonnelApprovalStation(TimestampMixin, db.Model):
    __tablename__ = "personnel_approval_stations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lifecycle_case_id = db.Column(db.Integer, db.ForeignKey("personnel_lifecycle_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    handover_id = db.Column(db.Integer, db.ForeignKey("personnel_handover_records.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    acted_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    module_name = db.Column(db.String(50), nullable=False, default="clearance", index=True)
    station_order = db.Column(db.Integer, nullable=False, default=1, index=True)
    station_name = db.Column(db.String(255), nullable=False)
    role_label = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    due_date = db.Column(db.Date, nullable=True, index=True)
    decision_note = db.Column(db.Text, nullable=True)
    decision_at = db.Column(db.DateTime, nullable=True, index=True)
    is_required = db.Column(db.Boolean, default=True, nullable=False, index=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_approval_stations", lazy="dynamic", cascade="all, delete-orphan"),
    )
    lifecycle_case = db.relationship(
        "PersonnelLifecycleCase",
        foreign_keys=[lifecycle_case_id],
        backref=db.backref("approval_stations", lazy="dynamic"),
    )
    handover = db.relationship(
        "PersonnelHandoverRecord",
        foreign_keys=[handover_id],
        backref=db.backref("approval_stations", lazy="dynamic"),
    )
    assigned_user = db.relationship(
        "User",
        foreign_keys=[assigned_user_id],
        backref=db.backref("assigned_personnel_approval_stations", lazy="dynamic"),
    )
    acted_by = db.relationship(
        "User",
        foreign_keys=[acted_by_id],
        backref=db.backref("acted_personnel_approval_stations", lazy="dynamic"),
    )


class PersonnelDigitalHandoverDocument(TimestampMixin, db.Model):
    __tablename__ = "personnel_digital_handover_documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lifecycle_case_id = db.Column(db.Integer, db.ForeignKey("personnel_lifecycle_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    handover_id = db.Column(db.Integer, db.ForeignKey("personnel_handover_records.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    signed_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    document_type = db.Column(db.String(50), nullable=False, default="devir_teslim", index=True)
    title = db.Column(db.String(255), nullable=False)
    document_no = db.Column(db.String(120), nullable=True, index=True)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    summary = db.Column(db.Text, nullable=True)
    content_text = db.Column(db.Text, nullable=True)
    hash_value = db.Column(db.String(128), nullable=True, index=True)
    signed_at = db.Column(db.DateTime, nullable=True, index=True)
    approved_at = db.Column(db.DateTime, nullable=True, index=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_digital_handover_documents", lazy="noload", cascade="save-update, merge",
            passive_deletes=True),
    )
    lifecycle_case = db.relationship(
        "PersonnelLifecycleCase",
        foreign_keys=[lifecycle_case_id],
        backref=db.backref("digital_handover_documents", lazy="dynamic"),
    )
    handover = db.relationship(
        "PersonnelHandoverRecord",
        foreign_keys=[handover_id],
        backref=db.backref("digital_documents", lazy="dynamic"),
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        backref=db.backref("created_personnel_digital_handover_documents", lazy="noload",
            passive_deletes=True,
            cascade="save-update, merge"),
    )
    signed_by = db.relationship(
        "User",
        foreign_keys=[signed_by_id],
        backref=db.backref("signed_personnel_digital_handover_documents", lazy="noload",
            passive_deletes=True,
            cascade="save-update, merge"),
    )
    approved_by = db.relationship(
        "User",
        foreign_keys=[approved_by_id],
        backref=db.backref("approved_personnel_digital_handover_documents", lazy="noload",
            passive_deletes=True,
            cascade="save-update, merge"),
    )


class PersonnelExitRiskAssessment(TimestampMixin, db.Model):
    __tablename__ = "personnel_exit_risk_assessments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lifecycle_case_id = db.Column(db.Integer, db.ForeignKey("personnel_lifecycle_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    assessed_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    risk_score = db.Column(db.Integer, nullable=False, default=0, index=True)
    risk_level = db.Column(db.String(20), nullable=False, default="dusuk", index=True)
    knowledge_loss_risk = db.Column(db.Integer, nullable=False, default=0)
    asset_risk = db.Column(db.Integer, nullable=False, default=0)
    access_risk = db.Column(db.Integer, nullable=False, default=0)
    process_risk = db.Column(db.Integer, nullable=False, default=0)
    note = db.Column(db.Text, nullable=True)
    mitigation_plan = db.Column(db.Text, nullable=True)
    assessed_at = db.Column(db.DateTime, nullable=True, index=True)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("personnel_exit_risk_assessments", lazy="dynamic", cascade="all, delete-orphan"),
    )
    lifecycle_case = db.relationship(
        "PersonnelLifecycleCase",
        foreign_keys=[lifecycle_case_id],
        backref=db.backref("exit_risk_assessments", lazy="dynamic"),
    )
    assessed_by = db.relationship(
        "User",
        foreign_keys=[assessed_by_id],
        backref=db.backref("assessed_personnel_exit_risks", lazy="dynamic"),
    )
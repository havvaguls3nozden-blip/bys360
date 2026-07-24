"""Performans donemi, degerlendirme ve snapshot modelleri."""

from datetime import date, datetime, time, timedelta

from app.core.datetime_utils import utc_now

from .base import TimestampMixin, db


class PerformancePeriod(TimestampMixin, db.Model):
    __tablename__ = "performance_periods"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    # BYS360_V55_MIGRATION_COMPAT_PERIOD_NAME_COLUMN: eski SQL aliasları için metadata uyumlu kolon.
    name = db.Column(db.String(255), nullable=True, index=True)
    period_type = db.Column(db.String(50), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    # BYS360_SCORING_AFTER_PERIOD_END_MODEL
    scoring_start_date = db.Column(db.DateTime, nullable=True)
    scoring_end_date = db.Column(db.DateTime, nullable=True)
    scoring_auto_start_after_period = db.Column(db.Boolean, nullable=False, default=True)
    evaluation_start_date = db.Column(db.Date, nullable=True, index=True)
    evaluation_end_date = db.Column(db.Date, nullable=True, index=True)
    evaluation_due_days = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)

    # BYS360_MEETING_P1_PERIOD_SCOPE_MODEL_COLUMNS
    scope_type = db.Column(db.String(40), default="all", nullable=False, index=True)
    scope_unit_label = db.Column(db.String(255), nullable=True)
    scope_category_label = db.Column(db.String(255), nullable=True, index=True)
    scope_personnel_filter = db.Column(db.Text, nullable=True)
    # BYS360_PHASE8_3_SPECIAL_SCENARIO_MODEL_COLUMN
    special_scenario_type = db.Column(db.String(60), nullable=True, index=True)
    level_3_column_visible = db.Column(db.Boolean, default=False, nullable=False)
    scorecard_readability_mode = db.Column(db.String(40), default="kurumsal", nullable=False)


    is_active = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    results_published = db.Column(db.Boolean, default=False, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)
    published_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    allow_feedback_requests = db.Column(db.Boolean, default=False, nullable=False)
    feedback_request_deadline = db.Column(db.Date, nullable=True)

    enable_level_3 = db.Column(db.Boolean, default=False, nullable=False)
    enable_level_3_scoring = db.Column(db.Boolean, default=False, nullable=False)
    require_level_3_completion_for_final = db.Column(db.Boolean, default=False, nullable=False)

    # Legacy fallback weights are retained for schema compatibility and bulk tools.
    # Runtime weighting should continue to use PerformanceWeightConfig.
    level_1_weight = db.Column(db.Numeric(5, 2), default=50.00, nullable=False)
    level_2_weight = db.Column(db.Numeric(5, 2), default=50.00, nullable=False)
    level_3_weight = db.Column(db.Numeric(5, 2), default=0.00, nullable=False)

    minimum_presence_days_for_evaluation = db.Column(db.Float, default=0.0, nullable=False)
    leave_skip_threshold_days = db.Column(db.Float, nullable=True)
    absence_skip_threshold_days = db.Column(db.Float, nullable=True)
    auto_skip_if_fully_absent = db.Column(db.Boolean, default=True, nullable=False)
    manager_delegation_required = db.Column(db.Boolean, default=True, nullable=False)

    snapshot_status = db.Column(
        db.String(30),
        nullable=False,
        default="not_started",
        index=True,
    )
    snapshot_generated_at = db.Column(db.DateTime, nullable=True)
    snapshot_generated_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
    )

    evaluations = db.relationship("PerformanceEvaluation", back_populates="period", lazy="dynamic")
    assignments = db.relationship("EvaluationAssignment", back_populates="period", lazy="dynamic")
    weight_configs = db.relationship("PerformanceWeightConfig", back_populates="period", lazy="dynamic")
    result_snapshots = db.relationship(
        "PerformanceResultSnapshot",
        back_populates="period",
        lazy="dynamic",
    )
    import_batches = db.relationship(
        "PerformanceImportBatch",
        back_populates="period",
        lazy="dynamic",
    )
    leave_requests = db.relationship(
        "PersonnelLeave",
        back_populates="period",
        lazy="dynamic",
    )
    attendance_exceptions = db.relationship(
        "AttendanceException",
        back_populates="period",
        lazy="dynamic",
    )
    snapshot_generated_by = db.relationship(
        "User",
        foreign_keys=[snapshot_generated_by_id],
        lazy="joined",
    )

    @property
    def level_3_mode(self) -> str:
        if not bool(self.enable_level_3):
            return "off"
        if bool(self.enable_level_3_scoring):
            return "scoring"
        return "comment_only"

    @property
    def evaluation_window_start(self):
        return self.evaluation_start_date or self.start_date

    @property
    def evaluation_window_end(self):
        return self.evaluation_end_date or self.end_date

    @property
    def evaluation_due_days_effective(self) -> int | None:
        raw = getattr(self, "evaluation_due_days", None)
        if raw is None:
            return None
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    def is_evaluation_open_on(self, check_date: date | None = None) -> bool:
        target = check_date or date.today()
        start = self.evaluation_window_start
        end = self.evaluation_window_end
        if start and target < start:
            return False
        return not (end and target > end)

    def build_due_datetime(self, assigned_at: datetime | None = None) -> datetime | None:
        anchor = assigned_at or utc_now()
        due_days = self.evaluation_due_days_effective
        due_dt = anchor + timedelta(days=due_days) if due_days else None
        window_end = self.evaluation_window_end
        if window_end:
            window_end_dt = datetime.combine(window_end, time(23, 59, 59))
            if due_dt is None or due_dt > window_end_dt:
                due_dt = window_end_dt
        return due_dt

    def __repr__(self):
        return f"<PerformancePeriod id={self.id} title={self.title} active={self.is_active} published={self.results_published}>"


class PerformanceCriteria(TimestampMixin, db.Model):
    __tablename__ = "performance_criteria"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    weight = db.Column(db.Float, default=20.0, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    criteria_code = db.Column(db.String(100), unique=True, nullable=True, index=True)
    effective_start_date = db.Column(db.Date, nullable=True)
    effective_end_date = db.Column(db.Date, nullable=True)

    items = db.relationship("PerformanceEvaluationItem", back_populates="criteria", lazy="dynamic")

    def __repr__(self):
        return f"<PerformanceCriteria {self.name}>"


class PerformanceWeightConfig(TimestampMixin, db.Model):
    __tablename__ = "performance_weight_configs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, default="Varsayılan")
    period_id = db.Column(db.Integer, db.ForeignKey("performance_periods.id"), nullable=True, index=True)

    evaluator_1_weight = db.Column(db.Float, default=50.0, nullable=False)
    evaluator_2_weight = db.Column(db.Float, default=50.0, nullable=False)
    evaluator_3_weight = db.Column(db.Float, default=0.0, nullable=False)

    level_3_enabled = db.Column(db.Boolean, default=False, nullable=False)
    level_3_mode = db.Column(db.String(20), default="comment_only", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    period = db.relationship("PerformancePeriod", back_populates="weight_configs")

    @property
    def total_weight(self) -> float:
        return float(self.evaluator_1_weight or 0) + float(self.evaluator_2_weight or 0) + float(self.evaluator_3_weight or 0)

    def __repr__(self):
        return (
            f"<PerformanceWeightConfig period={self.period_id} "
            f"weights={self.evaluator_1_weight}/{self.evaluator_2_weight}/{self.evaluator_3_weight} "
            f"mode={self.level_3_mode}>"
        )


class PerformanceEvaluation(TimestampMixin, db.Model):
    __tablename__ = "performance_evaluations"

    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey("performance_periods.id"), nullable=False, index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    level_1_evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    level_2_evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    level_3_evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    # eski deneme: reviewer_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    level_1_total_100 = db.Column(db.Float, default=0, nullable=False)
    level_2_total_100 = db.Column(db.Float, default=0, nullable=False)
    level_3_total_100 = db.Column(db.Float, default=0, nullable=False)
    final_total_100 = db.Column(db.Float, default=0, nullable=False)

    level_1_general_comment = db.Column(db.Text, nullable=True)
    level_2_general_comment = db.Column(db.Text, nullable=True)
    level_3_general_comment = db.Column(db.Text, nullable=True)

    level_1_completed = db.Column(db.Boolean, default=False, nullable=False)
    level_2_completed = db.Column(db.Boolean, default=False, nullable=False)
    level_3_completed = db.Column(db.Boolean, default=False, nullable=False)

    status = db.Column(db.String(50), default="bekliyor", nullable=False, index=True)
    workflow_status = db.Column(db.String(50), default="taslak_1_amir", nullable=False, index=True)
    level_1_submitted_to_level_2_at = db.Column(db.DateTime, nullable=True)
    level_2_seen_level_1_at = db.Column(db.DateTime, nullable=True)
    level_2_returned_to_level_1_at = db.Column(db.DateTime, nullable=True)
    level_2_return_note = db.Column(db.Text, nullable=True)
    level_2_returned_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    level_1_last_resubmitted_at = db.Column(db.DateTime, nullable=True)

    is_published_to_employee = db.Column(db.Boolean, default=False, nullable=False)
    published_to_employee_at = db.Column(db.DateTime, nullable=True)
    published_to_employee_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    employee_score_viewed_at = db.Column(db.DateTime, nullable=True)
    employee_score_acknowledged_at = db.Column(db.DateTime, nullable=True)
    employee_score_acknowledged_note = db.Column(db.Text, nullable=True)
    feedback_request_allowed = db.Column(db.Boolean, default=True, nullable=False)

    evaluation_exempted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    evaluation_exemption_reason = db.Column(db.String(255), nullable=True)
    employee_leave_days_in_period = db.Column(db.Float, default=0.0, nullable=False)
    employee_absence_days_in_period = db.Column(db.Float, default=0.0, nullable=False)
    employee_available_days_in_period = db.Column(db.Float, default=0.0, nullable=False)

    period = db.relationship("PerformancePeriod", back_populates="evaluations")
    employee = db.relationship("User", foreign_keys=[employee_id], back_populates="evaluations_as_employee")
    # Amir zinciri burada acik kalsin; debug ederken cok is goruyor.
    level_1_evaluator = db.relationship("User", foreign_keys=[level_1_evaluator_id], back_populates="evaluations_as_level_1")
    level_2_evaluator = db.relationship("User", foreign_keys=[level_2_evaluator_id], back_populates="evaluations_as_level_2")
    level_3_evaluator = db.relationship("User", foreign_keys=[level_3_evaluator_id], back_populates="evaluations_as_level_3")
    level_2_returned_by = db.relationship("User", foreign_keys=[level_2_returned_by_id])
    items = db.relationship(
        "PerformanceEvaluationItem",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    snapshots = db.relationship(
        "PerformanceResultSnapshot",
        back_populates="evaluation",
        lazy="dynamic",
    )

    __table_args__ = (
        db.UniqueConstraint("period_id", "employee_id", name="uq_period_employee_evaluation"),
    )

    @property
    def published_at(self):
        return self.published_to_employee_at

    @published_at.setter
    def published_at(self, value):
        self.published_to_employee_at = value

    @property
    def published_by_user_id(self):
        return self.published_to_employee_by_id

    @published_by_user_id.setter
    def published_by_user_id(self, value):
        self.published_to_employee_by_id = value

    def __repr__(self):
        return (
            f"<PerformanceEvaluation id={self.id} employee={self.employee_id} period={self.period_id} "
            f"status={self.status} final={self.final_total_100}>"
        )


class PerformanceEvaluationItem(TimestampMixin, db.Model):
    __tablename__ = "performance_evaluation_items"

    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("performance_evaluations.id"), nullable=False, index=True)
    criteria_id = db.Column(db.Integer, db.ForeignKey("performance_criteria.id"), nullable=False, index=True)
    manager_level = db.Column(db.Integer, nullable=False, index=True)
    score = db.Column(db.Float, nullable=True)
    # score nullable kaldı; eski importlarda boş satır görürsem uygulama çökmesin diye.
    # score_100, 1-5 arası puanın saklanan 100'lük karşılığıdır.
    score_100 = db.Column(db.Float, default=0.0, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    strength_note = db.Column(db.Text, nullable=True)
    justification = db.Column(db.Text, nullable=True)

    evaluation = db.relationship("PerformanceEvaluation", back_populates="items")
    criteria = db.relationship("PerformanceCriteria", back_populates="items")

    __table_args__ = (
        db.UniqueConstraint("evaluation_id", "criteria_id", "manager_level", name="uq_eval_criteria_level_item"),
    )

    def sync_score_100(self) -> float:
        try:
            raw_score = float(self.score) if self.score not in (None, "") else None
        except (TypeError, ValueError):
            raw_score = None

        if raw_score is None:
            self.score_100 = 0.0
            return self.score_100

        bounded = min(5.0, max(1.0, raw_score))
        self.score_100 = round(((bounded - 1.0) / 4.0) * 100.0, 2)
        return self.score_100

    def set_score(self, value) -> float:
        self.score = value
        return self.sync_score_100()

    def __repr__(self):
        return (
            f"<PerformanceEvaluationItem eval={self.evaluation_id} criteria={self.criteria_id} "
            f"level={self.manager_level} score={self.score} score100={self.score_100}>"
        )


class EvaluationAssignment(TimestampMixin, db.Model):
    __tablename__ = "evaluation_assignments"

    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey("performance_periods.id"), nullable=False, index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    original_evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    delegation_id = db.Column(db.Integer, db.ForeignKey("delegation_assignments.id"), nullable=True, index=True)
    assignment_source = db.Column(db.String(30), default="direct", nullable=False, index=True)
    coverage_note = db.Column(db.String(255), nullable=True)
    manager_level = db.Column(db.Integer, nullable=False, index=True)
    status = db.Column(db.String(50), default="bekliyor", nullable=False, index=True)
    assigned_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    period = db.relationship("PerformancePeriod", back_populates="assignments")
    employee = db.relationship("User", foreign_keys=[employee_id], back_populates="assigned_for_employee")
    evaluator = db.relationship("User", foreign_keys=[evaluator_id], back_populates="evaluation_assignments")
    original_evaluator = db.relationship("User", foreign_keys=[original_evaluator_id])
    delegation = db.relationship("DelegationAssignment", foreign_keys=[delegation_id])

    __table_args__ = (
        db.UniqueConstraint(
            "period_id",
            "employee_id",
            "evaluator_id",
            "manager_level",
            name="uq_period_employee_evaluator_level_assignment",
        ),
    )

    @property
    def is_completed(self) -> bool:
        return bool(self.completed_at) or (self.status or "").strip().lower() == "tamamlandi"

    @property
    def is_overdue(self) -> bool:
        if not self.due_date or self.is_completed:
            return False
        return utc_now() > self.due_date

    @property
    def is_due_soon(self) -> bool:
        if not self.due_date or self.is_completed or self.is_overdue:
            return False
        remaining = self.due_date - utc_now()
        return remaining.total_seconds() <= 2 * 24 * 60 * 60

    def __repr__(self):
        return f"<EvaluationAssignment employee={self.employee_id} evaluator={self.evaluator_id} lvl={self.manager_level}>"


class AssignmentCoverageLog(TimestampMixin, db.Model):
    __tablename__ = "assignment_coverage_logs"

    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey("performance_periods.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    manager_level = db.Column(db.Integer, nullable=True, index=True)
    event_scope = db.Column(db.String(30), default="generation", nullable=False, index=True)
    event_type = db.Column(db.String(30), nullable=False, index=True)
    severity = db.Column(db.String(20), default="warning", nullable=False, index=True)
    reason = db.Column(db.String(255), nullable=True)
    run_key = db.Column(db.String(40), nullable=True, index=True)
    original_evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    acting_evaluator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    delegation_id = db.Column(db.Integer, db.ForeignKey("delegation_assignments.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    period = db.relationship("PerformancePeriod", foreign_keys=[period_id])
    employee = db.relationship("User", foreign_keys=[employee_id])
    original_evaluator = db.relationship("User", foreign_keys=[original_evaluator_id])
    acting_evaluator = db.relationship("User", foreign_keys=[acting_evaluator_id])
    delegation = db.relationship("DelegationAssignment", foreign_keys=[delegation_id])
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="coverage_logs_created",
    )

    def __repr__(self):
        return (
            f"<AssignmentCoverageLog period={self.period_id} employee={self.employee_id} "
            f"type={self.event_type} level={self.manager_level}>"
        )

class PerformanceResultSnapshot(TimestampMixin, db.Model):
    __tablename__ = "performance_result_snapshots"

    id = db.Column(db.Integer, primary_key=True)

    period_id = db.Column(
        db.Integer,
        db.ForeignKey("performance_periods.id"),
        nullable=False,
        index=True,
    )
    evaluation_id = db.Column(
        db.Integer,
        db.ForeignKey("performance_evaluations.id"),
        nullable=True,
        index=True,
    )
    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    employee_name_snapshot = db.Column(db.String(255), nullable=False, index=True)
    sicil_no_snapshot = db.Column(db.String(50), nullable=False, index=True)

    organization_unit_id_snapshot = db.Column(db.Integer, nullable=True, index=True)
    organization_unit_code_snapshot = db.Column(db.String(100), nullable=True, index=True)
    birim_snapshot = db.Column(db.String(255), nullable=True, index=True)
    ust_birim_snapshot = db.Column(db.String(255), nullable=True, index=True)
    org_path_snapshot = db.Column(db.Text, nullable=True)

    manager_1_user_id_snapshot = db.Column(db.Integer, nullable=True, index=True)
    manager_1_name_snapshot = db.Column(db.String(255), nullable=True)
    manager_1_sicil_snapshot = db.Column(db.String(50), nullable=True, index=True)

    manager_2_user_id_snapshot = db.Column(db.Integer, nullable=True, index=True)
    manager_2_name_snapshot = db.Column(db.String(255), nullable=True)
    manager_2_sicil_snapshot = db.Column(db.String(50), nullable=True, index=True)

    manager_3_user_id_snapshot = db.Column(db.Integer, nullable=True, index=True)
    manager_3_name_snapshot = db.Column(db.String(255), nullable=True)
    manager_3_sicil_snapshot = db.Column(db.String(50), nullable=True, index=True)

    level_1_total_100 = db.Column(db.Float, default=0, nullable=False)
    level_2_total_100 = db.Column(db.Float, default=0, nullable=False)
    level_3_total_100 = db.Column(db.Float, default=0, nullable=False)
    final_total_100 = db.Column(db.Float, default=0, nullable=False)

    evaluation_status_snapshot = db.Column(db.String(50), nullable=True, index=True)

    ranking_in_unit = db.Column(db.Integer, nullable=True)
    ranking_in_scope = db.Column(db.Integer, nullable=True)

    level_1_general_comment = db.Column(db.Text, nullable=True)
    level_2_general_comment = db.Column(db.Text, nullable=True)
    level_3_general_comment = db.Column(db.Text, nullable=True)

    published_at = db.Column(db.DateTime, nullable=False, index=True)
    published_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
    )

    source_type = db.Column(
        db.String(50),
        nullable=False,
        default="system_published",
        index=True,
    )
    source_reference = db.Column(db.String(255), nullable=True)

    version_no = db.Column(db.Integer, nullable=False, default=1)
    is_current = db.Column(db.Boolean, default=True, nullable=False, index=True)

    payload_json = db.Column(db.JSON, nullable=True)

    period = db.relationship(
        "PerformancePeriod",
        back_populates="result_snapshots",
    )

    evaluation = db.relationship(
        "PerformanceEvaluation",
        back_populates="snapshots",
    )

    employee = db.relationship(
        "User",
        foreign_keys=[employee_id],
        back_populates="snapshots_as_employee",
    )

    published_by = db.relationship(
        "User",
        foreign_keys=[published_by_user_id],
        back_populates="snapshots_published",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "period_id",
            "employee_id",
            "version_no",
            name="uq_snapshot_period_employee_version",
        ),
    )

    def __repr__(self):
        return f"<PerformanceResultSnapshot employee={self.employee_id} period={self.period_id} version={self.version_no}>"


class PerformanceImportBatch(TimestampMixin, db.Model):
    __tablename__ = "performance_import_batches"

    id = db.Column(db.Integer, primary_key=True)

    import_type = db.Column(db.String(50), nullable=False, index=True)
    period_id = db.Column(
        db.Integer,
        db.ForeignKey("performance_periods.id"),
        nullable=False,
        index=True,
    )

    file_name = db.Column(db.String(255), nullable=True)
    status = db.Column(
        db.String(30),
        nullable=False,
        default="hazirlaniyor",
        index=True,
    )

    created_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )
    completed_at = db.Column(db.DateTime, nullable=True)

    row_count = db.Column(db.Integer, default=0, nullable=False)
    success_count = db.Column(db.Integer, default=0, nullable=False)
    error_count = db.Column(db.Integer, default=0, nullable=False)

    notes = db.Column(db.Text, nullable=True)

    period = db.relationship(
        "PerformancePeriod",
        back_populates="import_batches",
    )

    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="import_batches_created",
    )

    rows = db.relationship(
        "PerformanceImportBatchRow",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<PerformanceImportBatch id={self.id} type={self.import_type} status={self.status}>"


class PerformanceImportBatchRow(TimestampMixin, db.Model):
    __tablename__ = "performance_import_batch_rows"

    id = db.Column(db.Integer, primary_key=True)

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("performance_import_batches.id"),
        nullable=False,
        index=True,
    )

    row_no = db.Column(db.Integer, nullable=False)
    sicil_no = db.Column(db.String(50), nullable=True, index=True)
    employee_name_raw = db.Column(db.String(255), nullable=True)
    birim_raw = db.Column(db.String(255), nullable=True)
    ust_birim_raw = db.Column(db.String(255), nullable=True)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="bekliyor",
        index=True,
    )
    error_message = db.Column(db.Text, nullable=True)

    raw_payload_json = db.Column(db.JSON, nullable=True)

    batch = db.relationship(
        "PerformanceImportBatch",
        back_populates="rows",
    )

    def __repr__(self):
        return f"<PerformanceImportBatchRow batch={self.batch_id} row={self.row_no} status={self.status}>"


class PerformancePublishLog(db.Model):
    __tablename__ = "performance_publish_logs"

    id = db.Column(db.Integer, primary_key=True)

    period_id = db.Column(db.Integer, db.ForeignKey("performance_periods.id"), nullable=False)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("performance_evaluations.id"), nullable=True)

    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    action_type = db.Column(db.String(50), nullable=False)  # publish / unpublish / bulk_publish / bulk_unpublish
    note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    period = db.relationship("PerformancePeriod", foreign_keys=[period_id])
    evaluation = db.relationship("PerformanceEvaluation", foreign_keys=[evaluation_id])
    employee = db.relationship("User", foreign_keys=[employee_id])
    actor = db.relationship("User", foreign_keys=[actor_user_id])


# BYS360_MEETING_P2_ARCHIVE_NOTES_MODEL_NOTE
# Faz 8 arşiv ve ara not tabloları çalışma zamanı servisinde güvenli DDL ile hazırlanır:
# - performance_scorecard_archive
# - performance_interim_notes
# Bu not model dosyasında iz bırakmak için eklenmiştir; canlı DB değişikliği servis/gate ile yapılır.


# BYS360_MEETING_P3_REMINDERS_MODEL_NOTE
# Faz 9 hatırlatma/aksatan amir tabloları çalışma zamanı servisinde güvenli DDL ile hazırlanır:
# - performance_reminder_queue
# - performance_overdue_manager_snapshots
# Bu not model dosyasında iz bırakmak için eklenmiştir; canlı DB değişikliği servis/gate ile yapılır.

# BYS360_MEETING_P4_DEVELOPMENT_GUIDANCE_MODEL_NOTE
# Faz 10 gelişim önerisi/rehberlik tablosu çalışma zamanı servisinde güvenli DDL ile hazırlanır:
# - performance_development_recommendations
# Bu not model dosyasında iz bırakmak için eklenmiştir; canlı DB değişikliği servis/gate ile yapılır.

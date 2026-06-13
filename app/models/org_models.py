"""Organizasyon yapisi ve atama gecmisi modelleri."""

from .base import TimestampMixin, db


class OrganizationUnit(TimestampMixin, db.Model):
    __tablename__ = "organization_units"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    unit_type = db.Column(db.String(50), nullable=False, default="diger", index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("organization_units.id"), nullable=True, index=True)
    manager_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # eski deneme kalintisi: manager_sicil = db.Column(db.String(50), nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    unit_code = db.Column(db.String(100), unique=True, nullable=True, index=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    closure_reason = db.Column(db.String(255), nullable=True)
    successor_unit_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_units.id"),
        nullable=True,
        index=True,
    )

    # Agac baglari: ust birim <-> alt birimler
    parent = db.relationship(
        "OrganizationUnit",
        remote_side=[id],
        foreign_keys=[parent_id],
        back_populates="children",
    )

    successor_unit = db.relationship(
        "OrganizationUnit",
        remote_side=[id],
        foreign_keys=[successor_unit_id],
        uselist=False,
    )

    children = db.relationship(
        "OrganizationUnit",
        foreign_keys=[parent_id],
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="select",
    )

    manager = db.relationship(
        "User",
        foreign_keys=[manager_user_id],
        lazy="joined",
    )

    users = db.relationship(
        "User",
        foreign_keys="User.organization_unit_id",
        primaryjoin="OrganizationUnit.id == User.organization_unit_id",
        back_populates="organization_unit",
        lazy="dynamic",
    )

    versions = db.relationship(
        "OrganizationUnitVersion",
        back_populates="organization_unit",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    assignment_history = db.relationship(
        "EmployeeOrgAssignmentHistory",
        foreign_keys="EmployeeOrgAssignmentHistory.organization_unit_id",
        back_populates="organization_unit",
        lazy="dynamic",
    )

    def __repr__(self):
        parent_hint = self.parent_id if self.parent_id else "root"
        return f"<OrganizationUnit id={self.id} code={self.unit_code} name={self.name} parent={parent_hint}>"

class OrganizationUnitVersion(TimestampMixin, db.Model):
    __tablename__ = "organization_unit_versions"

    id = db.Column(db.Integer, primary_key=True)
    organization_unit_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_units.id"),
        nullable=False,
        index=True,
    )

    unit_code_snapshot = db.Column(db.String(100), nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    unit_type = db.Column(db.String(50), nullable=True, index=True)

    parent_unit_id_snapshot = db.Column(db.Integer, nullable=True, index=True)
    parent_name_snapshot = db.Column(db.String(255), nullable=True)
    org_path_snapshot = db.Column(db.Text, nullable=True)

    effective_start_date = db.Column(db.Date, nullable=False, index=True)
    effective_end_date = db.Column(db.Date, nullable=True, index=True)

    change_reason = db.Column(db.String(255), nullable=True)
    is_current = db.Column(db.Boolean, default=True, nullable=False, index=True)

    organization_unit = db.relationship(
        "OrganizationUnit",
        back_populates="versions",
    )

    assignment_history = db.relationship(
        "EmployeeOrgAssignmentHistory",
        foreign_keys="EmployeeOrgAssignmentHistory.organization_unit_version_id",
        back_populates="organization_unit_version",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<OrganizationUnitVersion unit={self.organization_unit_id} name={self.name}>"


class EmployeeOrgAssignmentHistory(TimestampMixin, db.Model):
    __tablename__ = "employee_org_assignment_history"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    organization_unit_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_units.id"),
        nullable=True,
        index=True,
    )
    # eski deneme kalintisi: department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))

    organization_unit_version_id = db.Column(
        db.Integer,
        db.ForeignKey("organization_unit_versions.id"),
        nullable=True,
        index=True,
    )

    unit_name_snapshot = db.Column(db.String(255), nullable=False, index=True)
    parent_unit_name_snapshot = db.Column(db.String(255), nullable=True, index=True)
    org_path_snapshot = db.Column(db.Text, nullable=True)

    manager_1_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    manager_2_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    manager_3_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    manager_1_name_snapshot = db.Column(db.String(255), nullable=True)
    manager_2_name_snapshot = db.Column(db.String(255), nullable=True)
    manager_3_name_snapshot = db.Column(db.String(255), nullable=True)

    manager_1_sicil_snapshot = db.Column(db.String(50), nullable=True, index=True)
    manager_2_sicil_snapshot = db.Column(db.String(50), nullable=True, index=True)
    manager_3_sicil_snapshot = db.Column(db.String(50), nullable=True, index=True)

    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=True, index=True)

    assignment_type = db.Column(db.String(50), nullable=True, index=True)
    reason = db.Column(db.String(255), nullable=True)
    is_current = db.Column(db.Boolean, default=True, nullable=False, index=True)

    employee = db.relationship(
        "User",
        foreign_keys=[employee_id],
        back_populates="org_assignment_history",
    )

    organization_unit = db.relationship(
        "OrganizationUnit",
        foreign_keys=[organization_unit_id],
        back_populates="assignment_history",
    )

    organization_unit_version = db.relationship(
        "OrganizationUnitVersion",
        foreign_keys=[organization_unit_version_id],
        back_populates="assignment_history",
    )

    manager_1_user = db.relationship("User", foreign_keys=[manager_1_user_id])
    manager_2_user = db.relationship("User", foreign_keys=[manager_2_user_id])
    manager_3_user = db.relationship("User", foreign_keys=[manager_3_user_id])

    def __repr__(self):
        return f"<EmployeeOrgAssignmentHistory employee={self.employee_id} unit={self.unit_name_snapshot}>"
from __future__ import annotations

from app.core.datetime_utils import utc_now
from .base import TimestampMixin, db


class PortalProfile(TimestampMixin, db.Model):
    __tablename__ = "portal_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    headline = db.Column(db.String(180), nullable=True)
    about_text = db.Column(db.Text, nullable=True)
    cover_image_url = db.Column(db.String(500), nullable=True)
    is_wall_enabled = db.Column(db.Boolean, nullable=False, default=True)
    default_post_visibility = db.Column(db.String(30), nullable=False, default="public", index=True)
    last_seen_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])


class PortalGroup(TimestampMixin, db.Model):
    __tablename__ = "portal_groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False, index=True)
    slug = db.Column(db.String(200), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    group_type = db.Column(db.String(30), nullable=False, default="official", index=True)
    visibility_scope = db.Column(db.String(30), nullable=False, default="members", index=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    requires_approval = db.Column(db.Boolean, nullable=False, default=True)

    owner = db.relationship("User", foreign_keys=[owner_user_id])


class PortalGroupMember(TimestampMixin, db.Model):
    __tablename__ = "portal_group_members"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("portal_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    member_role = db.Column(db.String(30), nullable=False, default="member", index=True)
    status = db.Column(db.String(30), nullable=False, default="active", index=True)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    group = db.relationship("PortalGroup", foreign_keys=[group_id], backref=db.backref("memberships", lazy="dynamic"))
    user = db.relationship("User", foreign_keys=[user_id])
    approved_by = db.relationship("User", foreign_keys=[approved_by_user_id])

    __table_args__ = (db.UniqueConstraint("group_id", "user_id", name="uq_portal_group_member"),)


class PortalPost(TimestampMixin, db.Model):
    __tablename__ = "portal_posts"

    id = db.Column(db.Integer, primary_key=True)
    author_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    # BYS360_PORTAL_PROFILE_WALL_V2_8_MODEL
    wall_owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey("portal_groups.id", ondelete="SET NULL"), nullable=True, index=True)
    title = db.Column(db.String(220), nullable=True)
    body = db.Column(db.Text, nullable=False)
    post_type = db.Column(db.String(40), nullable=False, default="normal", index=True)
    visibility_scope = db.Column(db.String(30), nullable=False, default="public", index=True)
    status = db.Column(db.String(30), nullable=False, default="published", index=True)
    comments_enabled = db.Column(db.Boolean, nullable=False, default=True)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_featured_home = db.Column(db.Boolean, nullable=False, default=False, index=True)
    target_unit_name = db.Column(db.String(180), nullable=True, index=True)
    target_upper_unit_name = db.Column(db.String(180), nullable=True, index=True)
    target_role_name = db.Column(db.String(80), nullable=True, index=True)
    published_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)
    hidden_at = db.Column(db.DateTime, nullable=True)
    hidden_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    hidden_reason = db.Column(db.String(500), nullable=True)

    author = db.relationship("User", foreign_keys=[author_user_id])
    wall_owner = db.relationship("User", foreign_keys=[wall_owner_user_id])
    group = db.relationship("PortalGroup", foreign_keys=[group_id])
    hidden_by = db.relationship("User", foreign_keys=[hidden_by_user_id])


class PortalPostAudience(TimestampMixin, db.Model):
    __tablename__ = "portal_post_audiences"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("portal_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    audience_type = db.Column(db.String(30), nullable=False, index=True)
    audience_value = db.Column(db.String(220), nullable=False, index=True)

    post = db.relationship("PortalPost", foreign_keys=[post_id], backref=db.backref("audiences", lazy="dynamic"))


class PortalPostAttachment(TimestampMixin, db.Model):
    __tablename__ = "portal_post_attachments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("portal_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(700), nullable=False)
    mime_type = db.Column(db.String(120), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    post = db.relationship("PortalPost", foreign_keys=[post_id], backref=db.backref("attachments", lazy="dynamic"))
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_user_id])


class PortalPostReaction(TimestampMixin, db.Model):
    __tablename__ = "portal_post_reactions"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("portal_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reaction_type = db.Column(db.String(30), nullable=False, default="like", index=True)

    post = db.relationship("PortalPost", foreign_keys=[post_id], backref=db.backref("reactions", lazy="dynamic"))
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (db.UniqueConstraint("post_id", "user_id", name="uq_portal_post_reaction_user"),)


class PortalPostComment(TimestampMixin, db.Model):
    __tablename__ = "portal_post_comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("portal_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    author_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    # BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_COMMENT_THREAD_FIELDS
    parent_comment_id = db.Column(db.Integer, db.ForeignKey("portal_post_comments.id", ondelete="CASCADE"), nullable=True, index=True)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="published", index=True)
    hidden_at = db.Column(db.DateTime, nullable=True)
    hidden_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    post = db.relationship("PortalPost", foreign_keys=[post_id], backref=db.backref("comments", lazy="dynamic"))
    author = db.relationship("User", foreign_keys=[author_user_id])
    parent = db.relationship(
        "PortalPostComment",
        remote_side=[id],
        foreign_keys=[parent_comment_id],
        backref=db.backref("replies", lazy="dynamic", cascade="all, delete-orphan"),
    )
    hidden_by = db.relationship("User", foreign_keys=[hidden_by_user_id])


class PortalCommentReaction(TimestampMixin, db.Model):
    __tablename__ = "portal_comment_reactions"

    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("portal_post_comments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reaction_type = db.Column(db.String(30), nullable=False, default="like", index=True)

    comment = db.relationship("PortalPostComment", foreign_keys=[comment_id], backref=db.backref("reactions", lazy="dynamic"))
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (db.UniqueConstraint("comment_id", "user_id", name="uq_portal_comment_reaction_user"),)

class PortalCommentMention(TimestampMixin, db.Model):
    # BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_MODEL
    __tablename__ = "portal_comment_mentions"

    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("portal_post_comments.id", ondelete="CASCADE"), nullable=False, index=True)
    mentioned_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mentioned_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type = db.Column(db.String(30), nullable=False, default="comment", index=True)

    comment = db.relationship("PortalPostComment", foreign_keys=[comment_id], backref=db.backref("mentions", lazy="dynamic", cascade="all, delete-orphan"))
    mentioned_user = db.relationship("User", foreign_keys=[mentioned_user_id])
    mentioned_by = db.relationship("User", foreign_keys=[mentioned_by_user_id])

    __table_args__ = (db.UniqueConstraint("comment_id", "mentioned_user_id", name="uq_portal_comment_mention_user"),)

class PortalSavedPost(TimestampMixin, db.Model):
    __tablename__ = "portal_saved_posts"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("portal_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    post = db.relationship("PortalPost", foreign_keys=[post_id])
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (db.UniqueConstraint("post_id", "user_id", name="uq_portal_saved_post_user"),)


class PortalPostReport(TimestampMixin, db.Model):
    __tablename__ = "portal_post_reports"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("portal_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="open", index=True)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_note = db.Column(db.String(500), nullable=True)

    post = db.relationship("PortalPost", foreign_keys=[post_id])
    reporter = db.relationship("User", foreign_keys=[reporter_user_id])
    resolved_by = db.relationship("User", foreign_keys=[resolved_by_user_id])


class PortalModerationLog(TimestampMixin, db.Model):
    __tablename__ = "portal_moderation_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("portal_posts.id", ondelete="SET NULL"), nullable=True, index=True)
    action_type = db.Column(db.String(50), nullable=False, index=True)
    note = db.Column(db.String(500), nullable=True)

    actor = db.relationship("User", foreign_keys=[actor_user_id])
    post = db.relationship("PortalPost", foreign_keys=[post_id])


class PortalPinnedPost(TimestampMixin, db.Model):
    __tablename__ = "portal_pinned_posts"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("portal_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    pinned_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    pin_scope = db.Column(db.String(30), nullable=False, default="home", index=True)
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    post = db.relationship("PortalPost", foreign_keys=[post_id])
    pinned_by = db.relationship("User", foreign_keys=[pinned_by_user_id])


class PortalActivityLog(TimestampMixin, db.Model):
    __tablename__ = "portal_activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    action_type = db.Column(db.String(50), nullable=False, index=True)
    summary = db.Column(db.String(500), nullable=True)

    actor = db.relationship("User", foreign_keys=[actor_user_id])

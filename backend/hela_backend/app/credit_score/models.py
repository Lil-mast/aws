"""
app/credit_score/models.py
──────────────────────────
ScoreSnapshot, ScoreFactor, and ScoreEvent models.

Indexed on (user_id, created_at/calculated_at) for fast history queries per
the architecture spec in tech.md.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class ScoreSnapshot(Base):
    """
    A point-in-time capture of a user's Hela Score.

    One snapshot is created each time the scoring engine runs.
    The latest snapshot is the user's current score.
    """

    __tablename__ = "score_snapshots"
    __table_args__ = (
        Index("ix_score_snapshots_user_calculated", "user_id", "calculated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)          # 300–850
    tier: Mapped[str] = mapped_column(String(20), nullable=False)        # building|fair|good|strong|excellent
    engine_version: Mapped[int] = mapped_column(Integer, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    factors: Mapped[list["ScoreFactor"]] = relationship(
        "ScoreFactor", back_populates="snapshot", cascade="all, delete-orphan"
    )


class ScoreFactor(Base):
    """
    Per-factor breakdown stored alongside each ScoreSnapshot.

    Five rows per snapshot — one for each scoring dimension.
    """

    __tablename__ = "score_factors"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("score_snapshots.id", ondelete="CASCADE")
    )
    # Factor name matches keys in scoring_engine.FACTOR_WEIGHTS
    factor: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)   # 0.0–1.0
    sub_score: Mapped[int] = mapped_column(Integer, nullable=False)         # 0–100 normalised
    weighted_contribution: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    snapshot: Mapped["ScoreSnapshot"] = relationship("ScoreSnapshot", back_populates="factors")


class ScoreEvent(Base):
    """
    Individual decisions that moved the score.

    Every point change is recorded here so the user can see exactly what
    happened and why (the Decision Impact Feed).
    """

    __tablename__ = "score_events"
    __table_args__ = (
        Index("ix_score_events_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    # e.g. bill_paid_early | savings_target_met | budget_adhered | loan_cleared_early
    #       fuliza_overuse | bill_missed | budget_overspent
    points_delta: Mapped[int] = mapped_column(Integer, nullable=False)   # positive or negative
    reason: Mapped[str] = mapped_column(Text, nullable=False)            # human-readable
    # Optional link back to the triggering entity (transaction id, budget id, etc.)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    engine_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)

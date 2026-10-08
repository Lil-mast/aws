"""
app/transactions/models.py
──────────────────────────
Transaction storage and categorisation.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Core fields
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="KES")
    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'credit' | 'debit'
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sub_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Source tracking (M-Pesa, manual, etc.)
    source: Mapped[str] = mapped_column(String(50), default="manual")  # mpesa | manual
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )

    # Dates
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Scoring linkage flags
    is_bill_payment: Mapped[bool] = mapped_column(default=False)
    is_loan_repayment: Mapped[bool] = mapped_column(default=False)
    is_savings: Mapped[bool] = mapped_column(default=False)
    # Fuliza / mobile loan indicator
    is_fuliza: Mapped[bool] = mapped_column(default=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_early: Mapped[bool | None] = mapped_column(nullable=True)

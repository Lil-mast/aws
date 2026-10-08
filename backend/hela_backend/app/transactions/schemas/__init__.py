"""
app/transactions/schemas/__init__.py
─────────────────────────────────────
Pydantic schemas for transactions.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str = "KES"
    transaction_type: str  # credit | debit
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    source: str = "manual"
    external_id: Optional[str] = None
    transaction_date: date
    is_bill_payment: bool = False
    is_loan_repayment: bool = False
    is_savings: bool = False
    is_fuliza: bool = False
    due_date: Optional[date] = None
    paid_early: Optional[bool] = None


class TransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    currency: str
    transaction_type: str
    category: Optional[str]
    sub_category: Optional[str]
    description: Optional[str]
    reference: Optional[str]
    source: str
    transaction_date: date
    is_bill_payment: bool
    is_loan_repayment: bool
    is_savings: bool
    is_fuliza: bool
    due_date: Optional[date]
    paid_early: Optional[bool]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionSummary(BaseModel):
    total_credits: float
    total_debits: float
    net: float
    count: int
    by_category: dict[str, float]

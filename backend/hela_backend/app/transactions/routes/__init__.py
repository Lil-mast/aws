"""
app/transactions/routes/__init__.py
─────────────────────────────────────
Transaction CRUD + summary.

Routes (prefixed /api/v1/transactions):
  GET   /          - list transactions (paginated, filterable)
  POST  /          - create transaction
  GET   /summary   - aggregated summary
  GET   /{id}      - single transaction
  DELETE /{id}     - delete transaction
"""

import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.transactions.models import Transaction
from app.transactions.schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionSummary,
)
from app.users.models import User
from core.database import get_db
from core.security import get_current_user

router = APIRouter(tags=["transactions"])


@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    transaction_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the authenticated user's transactions with optional filters."""
    q = select(Transaction).where(Transaction.user_id == current_user.id)
    if transaction_type:
        q = q.where(Transaction.transaction_type == transaction_type)
    if category:
        q = q.where(Transaction.category == category)
    if from_date:
        q = q.where(Transaction.transaction_date >= from_date)
    if to_date:
        q = q.where(Transaction.transaction_date <= to_date)
    q = q.order_by(Transaction.transaction_date.desc()).offset(skip).limit(limit)

    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    body: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a new transaction."""
    tx = Transaction(user_id=current_user.id, **body.model_dump())
    db.add(tx)
    await db.flush()
    return tx


@router.get("/summary", response_model=TransactionSummary)
async def transaction_summary(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated credit/debit totals and per-category breakdown."""
    q = select(Transaction).where(Transaction.user_id == current_user.id)
    if from_date:
        q = q.where(Transaction.transaction_date >= from_date)
    if to_date:
        q = q.where(Transaction.transaction_date <= to_date)

    result = await db.execute(q)
    txs = result.scalars().all()

    total_credits = sum(float(t.amount) for t in txs if t.transaction_type == "credit")
    total_debits = sum(float(t.amount) for t in txs if t.transaction_type == "debit")
    by_category: dict[str, float] = {}
    for t in txs:
        if t.category:
            by_category[t.category] = by_category.get(t.category, 0) + float(t.amount)

    return TransactionSummary(
        total_credits=total_credits,
        total_debits=total_debits,
        net=total_credits - total_debits,
        count=len(txs),
        by_category=by_category,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return tx


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    await db.delete(tx)

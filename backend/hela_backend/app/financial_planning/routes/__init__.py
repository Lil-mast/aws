"""
app/financial_planning/routes/__init__.py
─────────────────────────────────────────
Budget, income, expense, and savings plan endpoints.

Routes (prefixed /api/v1/financial):
  GET   /budgets/              list budgets
  POST  /budgets/create        create budget
  GET   /budgets/{id}          budget details + categories
  DELETE /budgets/{id}         delete budget

  GET   /incomes/              list incomes
  POST  /incomes/create        record income

  GET   /expenses/             list expenses
  POST  /expenses/create       record expense

  GET   /savings/              list savings plans
  POST  /savings/create        create savings plan
  PATCH /savings/{id}          update progress
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.financial_planning.models import Budget, BudgetCategory, Expense, Income, SavingsPlan
from app.financial_planning.schemas import (
    BudgetCreate,
    BudgetResponse,
    ExpenseCreate,
    ExpenseResponse,
    IncomeCreate,
    IncomeResponse,
    SavingsPlanCreate,
    SavingsPlanResponse,
    SavingsPlanUpdate,
)
from app.users.models import User
from core.database import get_db
from core.security import get_current_user

router = APIRouter(tags=["financial_planning"])


# ── Budgets ───────────────────────────────────────────────────────────────────

@router.get("/budgets", response_model=List[BudgetResponse])
async def list_budgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Budget).where(Budget.user_id == current_user.id).order_by(Budget.created_at.desc())
    )
    budgets = result.scalars().all()
    # Eager-load categories
    for budget in budgets:
        cat_result = await db.execute(
            select(BudgetCategory).where(BudgetCategory.budget_id == budget.id)
        )
        budget.categories = cat_result.scalars().all()
    return budgets


@router.post("/budgets/create", response_model=BudgetResponse, status_code=201)
async def create_budget(
    body: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    budget = Budget(
        user_id=current_user.id,
        name=body.name,
        period=body.period,
        start_date=body.start_date,
        end_date=body.end_date,
        total_income=body.total_income,
        currency=body.currency,
    )
    db.add(budget)
    await db.flush()

    for cat in body.categories:
        db.add(BudgetCategory(budget_id=budget.id, **cat.model_dump()))
    await db.flush()

    # reload categories
    cat_result = await db.execute(
        select(BudgetCategory).where(BudgetCategory.budget_id == budget.id)
    )
    budget.categories = cat_result.scalars().all()
    return budget


@router.get("/budgets/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found.")
    cat_result = await db.execute(
        select(BudgetCategory).where(BudgetCategory.budget_id == budget.id)
    )
    budget.categories = cat_result.scalars().all()
    return budget


@router.delete("/budgets/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found.")
    await db.delete(budget)


# ── Income ────────────────────────────────────────────────────────────────────

@router.get("/incomes", response_model=List[IncomeResponse])
async def list_incomes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Income).where(Income.user_id == current_user.id).order_by(Income.income_date.desc())
    )
    return result.scalars().all()


@router.post("/incomes/create", response_model=IncomeResponse, status_code=201)
async def create_income(
    body: IncomeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    income = Income(user_id=current_user.id, **body.model_dump())
    db.add(income)
    await db.flush()
    return income


# ── Expenses ──────────────────────────────────────────────────────────────────

@router.get("/expenses", response_model=List[ExpenseResponse])
async def list_expenses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.expense_date.desc())
    )
    return result.scalars().all()


@router.post("/expenses/create", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    body: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    expense = Expense(user_id=current_user.id, **body.model_dump())
    db.add(expense)
    await db.flush()
    return expense


# ── Savings Plans ─────────────────────────────────────────────────────────────

@router.get("/savings", response_model=List[SavingsPlanResponse])
async def list_savings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavingsPlan)
        .where(SavingsPlan.user_id == current_user.id)
        .order_by(SavingsPlan.created_at.desc())
    )
    return result.scalars().all()


@router.post("/savings/create", response_model=SavingsPlanResponse, status_code=201)
async def create_savings_plan(
    body: SavingsPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = SavingsPlan(user_id=current_user.id, **body.model_dump())
    db.add(plan)
    await db.flush()
    return plan


@router.patch("/savings/{plan_id}", response_model=SavingsPlanResponse)
async def update_savings_plan(
    plan_id: uuid.UUID,
    body: SavingsPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavingsPlan).where(
            SavingsPlan.id == plan_id, SavingsPlan.user_id == current_user.id
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Savings plan not found.")
    if body.current_amount is not None:
        plan.current_amount = body.current_amount
    if body.is_completed is not None:
        plan.is_completed = body.is_completed
    if body.target_date is not None:
        plan.target_date = body.target_date
    await db.flush()
    return plan

"""
app/financial_planning/schemas/__init__.py
──────────────────────────────────────────
Pydantic schemas for budgets, categories, income, expenses, and savings plans.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Budget ────────────────────────────────────────────────────────────────────

class BudgetCategoryIn(BaseModel):
    name: str
    category_type: str = "needs"   # needs | wants | savings
    allocated_amount: float = Field(gt=0)


class BudgetCreate(BaseModel):
    name: str
    period: str = "monthly"
    start_date: date
    end_date: Optional[date] = None
    total_income: float = Field(ge=0)
    currency: str = "KES"
    categories: List[BudgetCategoryIn] = []


class BudgetCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    category_type: str
    allocated_amount: float
    spent_amount: float

    model_config = {"from_attributes": True}


class BudgetResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    period: str
    start_date: date
    end_date: Optional[date]
    total_income: float
    currency: str
    is_active: bool
    created_at: datetime
    categories: List[BudgetCategoryResponse] = []

    model_config = {"from_attributes": True}


# ── Income ────────────────────────────────────────────────────────────────────

class IncomeCreate(BaseModel):
    source: str
    amount: float = Field(gt=0)
    currency: str = "KES"
    income_date: date
    is_recurring: bool = False
    notes: Optional[str] = None


class IncomeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source: str
    amount: float
    currency: str
    income_date: date
    is_recurring: bool
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Expense ───────────────────────────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    category: str
    amount: float = Field(gt=0)
    currency: str = "KES"
    expense_date: date
    description: Optional[str] = None
    is_recurring: bool = False


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    amount: float
    currency: str
    expense_date: date
    description: Optional[str]
    is_recurring: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── SavingsPlan ───────────────────────────────────────────────────────────────

class SavingsPlanCreate(BaseModel):
    name: str
    goal_amount: float = Field(gt=0)
    currency: str = "KES"
    target_date: Optional[date] = None


class SavingsPlanUpdate(BaseModel):
    current_amount: Optional[float] = None
    is_completed: Optional[bool] = None
    target_date: Optional[date] = None


class SavingsPlanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    goal_amount: float
    current_amount: float
    currency: str
    target_date: Optional[date]
    is_completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}

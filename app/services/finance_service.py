import calendar
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func, extract
from app.extensions import db
from app.models.financial import (
    Income,
    Expense,
    ExpenseCategory,
    Budget,
    Savings,
    FinancialGoal,
    FinancialAlert
)
from app.models.user import User


class FinanceService:
    @staticmethod
    def get_monthly_summary(user_id: int, year: int, month: int) -> Dict[str, Any]:
        """Calculates monthly financial metrics for a user."""
        # Total Income for the month
        income_query = db.session.query(func.coalesce(func.sum(Income.amount), 0.0)).filter(
            Income.user_id == user_id,
            extract("year", Income.date) == year,
            extract("month", Income.date) == month
        ).scalar()
        total_income = float(income_query or 0.0)

        # Total Expense for the month
        expense_query = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
            Expense.user_id == user_id,
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month
        ).scalar()
        total_expense = float(expense_query or 0.0)

        # Total Savings for the month
        savings_query = db.session.query(func.coalesce(func.sum(Savings.amount), 0.0)).filter(
            Savings.user_id == user_id,
            extract("year", Savings.date) == year,
            extract("month", Savings.date) == month
        ).scalar()
        total_savings = float(savings_query or 0.0)

        # Cumulative Savings all time
        cum_savings_query = db.session.query(func.coalesce(func.sum(Savings.amount), 0.0)).filter(
            Savings.user_id == user_id
        ).scalar()
        cumulative_savings = float(cum_savings_query or 0.0)

        # Net cashflow and ratios
        net_cashflow = round(total_income - total_expense, 2)
        savings_rate = round((total_savings / total_income * 100), 1) if total_income > 0 else 0.0
        expense_to_income_ratio = round((total_expense / total_income * 100), 1) if total_income > 0 else 0.0

        # Days in month & average daily spending
        _, days_in_month = calendar.monthrange(year, month)
        today = date.today()
        if today.year == year and today.month == month:
            effective_days = max(1, today.day)
        else:
            effective_days = days_in_month
        avg_daily_spending = round(total_expense / effective_days, 2)

        # Category-wise spending
        cat_spending_raw = db.session.query(
            ExpenseCategory.id,
            ExpenseCategory.name,
            ExpenseCategory.type,
            func.coalesce(func.sum(Expense.amount), 0.0).label("cat_total")
        ).join(
            Expense, Expense.category_id == ExpenseCategory.id
        ).filter(
            Expense.user_id == user_id,
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month
        ).group_by(
            ExpenseCategory.id, ExpenseCategory.name, ExpenseCategory.type
        ).order_by(
            func.sum(Expense.amount).desc()
        ).all()

        categories_breakdown = []
        highest_category = {"name": "None", "amount": 0.0, "percentage": 0.0}

        for cat_id, cat_name, cat_type, cat_total in cat_spending_raw:
            cat_amt = float(cat_total)
            pct = round((cat_amt / total_expense * 100), 1) if total_expense > 0 else 0.0
            cat_obj = {
                "category_id": cat_id,
                "category_name": cat_name,
                "category_type": cat_type,
                "amount": cat_amt,
                "percentage": pct
            }
            categories_breakdown.append(cat_obj)

        if categories_breakdown:
            highest_category = categories_breakdown[0]

        return {
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "total_income": total_income,
            "total_expense": total_expense,
            "total_savings": total_savings,
            "cumulative_savings": cumulative_savings,
            "net_cashflow": net_cashflow,
            "savings_rate": savings_rate,
            "expense_to_income_ratio": expense_to_income_ratio,
            "avg_daily_spending": avg_daily_spending,
            "categories_breakdown": categories_breakdown,
            "highest_category": highest_category
        }

    @staticmethod
    def get_budget_status(user_id: int, year: int, month: int) -> Dict[str, Any]:
        """Calculates budget performance and compares with actual spending."""
        budgets = Budget.query.filter_by(user_id=user_id, year=year, month=month).all()

        # Overall budget (category_id is None)
        overall_budget_entry = next((b for b in budgets if b.category_id is None), None)
        overall_budget_amount = overall_budget_entry.amount if overall_budget_entry else 0.0

        # Expenses by category for this month
        cat_expenses = dict(
            db.session.query(
                Expense.category_id,
                func.coalesce(func.sum(Expense.amount), 0.0)
            ).filter(
                Expense.user_id == user_id,
                extract("year", Expense.date) == year,
                extract("month", Expense.date) == month
            ).group_by(Expense.category_id).all()
        )

        total_budgeted = 0.0
        total_actual_spent = 0.0
        category_budgets = []
        warnings = []

        for b in budgets:
            if b.category_id is not None:
                spent = float(cat_expenses.get(b.category_id, 0.0))
                remaining = round(b.amount - spent, 2)
                utilization = round((spent / b.amount * 100), 1) if b.amount > 0 else 0.0
                is_overspent = spent > b.amount
                overspent_amt = round(spent - b.amount, 2) if is_overspent else 0.0

                cat_name = b.category.name if b.category else "Custom"
                item = {
                    "budget_id": b.id,
                    "category_id": b.category_id,
                    "category_name": cat_name,
                    "budget_amount": b.amount,
                    "spent_amount": spent,
                    "remaining_amount": remaining,
                    "utilization_percentage": utilization,
                    "is_overspent": is_overspent,
                    "overspent_amount": overspent_amt
                }
                category_budgets.append(item)
                total_budgeted += b.amount
                total_actual_spent += spent

                if is_overspent:
                    warnings.append(f"{cat_name} spending has exceeded your monthly budget by {overspent_amt:.2f}.")
                elif utilization >= 80:
                    warnings.append(f"{cat_name} budget is {utilization}% used.")

        # If overall budget is set, compare against total expenses
        monthly_expense_total = float(
            db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
                Expense.user_id == user_id,
                extract("year", Expense.date) == year,
                extract("month", Expense.date) == month
            ).scalar() or 0.0
        )

        effective_budget = overall_budget_amount if overall_budget_amount > 0 else total_budgeted
        effective_spent = monthly_expense_total if overall_budget_amount > 0 else total_actual_spent
        remaining_budget = round(effective_budget - effective_spent, 2)
        overall_utilization = round((effective_spent / effective_budget * 100), 1) if effective_budget > 0 else 0.0

        if effective_budget > 0 and effective_spent > effective_budget:
            warnings.insert(0, f"Total spending has exceeded your monthly budget by {effective_spent - effective_budget:.2f}.")
        elif effective_budget > 0 and overall_utilization >= 85:
            warnings.insert(0, f"Overall monthly budget is {overall_utilization}% utilized.")

        return {
            "overall_budget_amount": overall_budget_amount,
            "effective_budget": effective_budget,
            "effective_spent": effective_spent,
            "remaining_budget": remaining_budget,
            "overall_utilization": overall_utilization,
            "category_budgets": category_budgets,
            "warnings": warnings,
            "has_budget": effective_budget > 0
        }

    @staticmethod
    def get_emergency_fund_status(user: User) -> Dict[str, Any]:
        """Calculates emergency fund guidance metrics."""
        # Total savings all time
        total_savings = float(
            db.session.query(func.coalesce(func.sum(Savings.amount), 0.0)).filter(
                Savings.user_id == user.id
            ).scalar() or 0.0
        )

        # Average monthly expense over past 3 months
        today = date.today()
        three_months_ago = today - timedelta(days=90)
        recent_expenses = float(
            db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
                Expense.user_id == user.id,
                Expense.date >= three_months_ago
            ).scalar() or 0.0
        )
        avg_monthly_expense = max(100.0, round(recent_expenses / 3, 2))

        # Target amount (user target, or recommended 6 months of expenses)
        recommended_target = round(avg_monthly_expense * 6, 2)
        target = user.emergency_fund_target if user.emergency_fund_target > 0 else recommended_target
        
        remaining = max(0.0, round(target - total_savings, 2))
        progress_pct = min(100.0, round((total_savings / target * 100), 1)) if target > 0 else 100.0
        runway_months = round(total_savings / avg_monthly_expense, 1) if avg_monthly_expense > 0 else 0.0

        return {
            "current_savings": total_savings,
            "target": target,
            "recommended_target": recommended_target,
            "remaining": remaining,
            "progress_percentage": progress_pct,
            "avg_monthly_expense": avg_monthly_expense,
            "runway_months": runway_months
        }

    @staticmethod
    def get_spending_trends(user_id: int, months_count: int = 6) -> List[Dict[str, Any]]:
        """Calculates month-by-month spending trends for the last N months."""
        today = date.today()
        trends = []

        for i in range(months_count - 1, -1, -1):
            # Calculate target year and month
            total_month = today.year * 12 + today.month - 1 - i
            yr = total_month // 12
            mo = (total_month % 12) + 1

            inc = float(
                db.session.query(func.coalesce(func.sum(Income.amount), 0.0)).filter(
                    Income.user_id == user_id,
                    extract("year", Income.date) == yr,
                    extract("month", Income.date) == mo
                ).scalar() or 0.0
            )

            exp = float(
                db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
                    Expense.user_id == user_id,
                    extract("year", Expense.date) == yr,
                    extract("month", Expense.date) == mo
                ).scalar() or 0.0
            )

            sav = float(
                db.session.query(func.coalesce(func.sum(Savings.amount), 0.0)).filter(
                    Savings.user_id == user_id,
                    extract("year", Savings.date) == yr,
                    extract("month", Savings.date) == mo
                ).scalar() or 0.0
            )

            month_abbr = calendar.month_abbr[mo]
            label = f"{month_abbr} {yr}"

            trends.append({
                "year": yr,
                "month": mo,
                "label": label,
                "income": inc,
                "expense": exp,
                "savings": sav,
                "net": round(inc - exp, 2)
            })

        return trends

    @staticmethod
    def evaluate_financial_health_score(user: User, year: int, month: int) -> Dict[str, Any]:
        """
        Evaluates overall financial health:
        Statuses: Healthy, Needs Attention, Needs Improvement.
        Includes indicators and explicit explanation of why.
        """
        summary = FinanceService.get_monthly_summary(user.id, year, month)
        budget_info = FinanceService.get_budget_status(user.id, year, month)
        emergency_info = FinanceService.get_emergency_fund_status(user)

        income = summary["total_income"] or user.monthly_income
        expense = summary["total_expense"]
        savings_rate = summary["savings_rate"]
        exp_ratio = summary["expense_to_income_ratio"]
        runway = emergency_info["runway_months"]
        utilization = budget_info["overall_utilization"]

        # Points scoring system (out of 100)
        score = 0
        reasons = []

        # 1. Savings Rate (max 25 pts)
        if savings_rate >= 20.0:
            score += 25
            reasons.append(f"Excellent savings rate of {savings_rate}% (healthy threshold: 20%+).")
        elif savings_rate >= 10.0:
            score += 15
            reasons.append(f"Moderate savings rate of {savings_rate}%. Aim to build towards 20% to accelerate wealth creation.")
        else:
            score += 5
            reasons.append(f"Low savings rate ({savings_rate}%). Less than 10% of monthly income is currently being retained.")

        # 2. Expense-to-Income Ratio (max 25 pts)
        if income > 0:
            if exp_ratio <= 70.0:
                score += 25
                reasons.append(f"Healthy expense-to-income ratio of {exp_ratio}% (recommended below 70%).")
            elif exp_ratio <= 90.0:
                score += 15
                reasons.append(f"Expense ratio is high ({exp_ratio}%). Discretionary spending may be squeezing savings room.")
            else:
                score += 5
                reasons.append(f"Critical expense ratio ({exp_ratio}%). Expenses are dangerously close to or exceeding income.")
        else:
            reasons.append("No active monthly income logged for this period.")

        # 3. Budget Discipline (max 25 pts)
        if budget_info["has_budget"]:
            if utilization <= 90.0:
                score += 25
                reasons.append(f"Strong budget discipline: spending is at {utilization}% of your allocated monthly budget.")
            elif utilization <= 100.0:
                score += 18
                reasons.append(f"Budget is nearly maxed out at {utilization}%. Exercise caution for remainder of period.")
            else:
                score += 5
                reasons.append(f"Over budget by {utilization - 100:.1f}%. Certain category limits were breached.")
        else:
            score += 15
            reasons.append("No strict budget limits configured yet. Setting category budgets helps control unplanned leaks.")

        # 4. Emergency Fund Runway (max 25 pts)
        if runway >= 6.0:
            score += 25
            reasons.append(f"Robust emergency reserve: {runway} months of living expenses safely funded.")
        elif runway >= 3.0:
            score += 15
            reasons.append(f"Moderate emergency cushion: {runway} months saved. Aim for a full 6 months buffer.")
        else:
            score += 5
            reasons.append(f"Under-protected emergency fund: only {runway} months of expenses covered. Prioritize liquidity.")

        # Overall Status
        if score >= 75:
            status = "Healthy"
            badge_class = "success"
        elif score >= 50:
            status = "Needs Attention"
            badge_class = "warning"
        else:
            status = "Needs Improvement"
            badge_class = "danger"

        return {
            "score": score,
            "status": status,
            "badge_class": badge_class,
            "reasons": reasons,
            "metrics": {
                "savings_rate": savings_rate,
                "expense_to_income_ratio": exp_ratio,
                "budget_utilization": utilization,
                "runway_months": runway
            }
        }
